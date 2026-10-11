from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction

from .models import Process, Message, Checkpoint, Event


# ==========================================
# 1. DASHBOARD
# ==========================================

def dashboard(request):

    processes = Process.objects.all()
    messages_list = Message.objects.select_related(
        "sender", "receiver"
    ).all()

    checkpoints = Checkpoint.objects.select_related(
        "process"
    ).all()

    events = Event.objects.all()[:20]

    context = {
        "processes": processes,
        "messages": messages_list,
        "checkpoints": checkpoints,
        "events": events,
    }

    return render(request, "dashboard.html", context)


# ==========================================
# 2. CREATE PROCESS
# ==========================================

def create_process(request):

    if request.method == "POST":

        name = request.POST.get("name")
        state = request.POST.get("state", 0)

        if not name:
            messages.error(request, "Process name is required.")
            return redirect("dashboard")

        if Process.objects.filter(name=name).exists():
            messages.error(request, "Process already exists.")
            return redirect("dashboard")

        process = Process.objects.create(
            name=name,
            state=int(state),
            status="RUNNING"
        )

        Event.objects.create(
            event_type="PROCESS_CREATED",
            description=f"Process {process.name} created."
        )

        messages.success(
            request,
            f"Process {process.name} created successfully."
        )

        return redirect("dashboard")

    return redirect("dashboard")


# ==========================================
# 3. SEND MESSAGE
# ==========================================

def send_message(request):

    if request.method == "POST":

        sender_id = request.POST.get("sender")
        receiver_id = request.POST.get("receiver")
        data = request.POST.get("data")
        amount = request.POST.get("amount", 10)

        sender = get_object_or_404(Process, id=sender_id)
        receiver = get_object_or_404(Process, id=receiver_id)

        # Sender failed hai to message nahi bhej sakta
        if sender.status == "FAILED":

            messages.error(
                request,
                f"{sender.name} is failed and cannot send message."
            )

            return redirect("dashboard")

        # Receiver failed hai
        if receiver.status == "FAILED":

            messages.error(
                request,
                f"{receiver.name} is failed and cannot receive message."
            )

            return redirect("dashboard")

        message_obj = Message.objects.create(
            sender=sender,
            receiver=receiver,
            data=data,
            amount=int(amount),
            delivered=True
        )

        # Receiver ki state update
        receiver.state += int(amount)
        receiver.save()

        # Event create
        Event.objects.create(
            event_type="MESSAGE_SENT",
            description=(
                f"{sender.name} sent {amount} to "
                f"{receiver.name} | Data: {data}"
            )
        )

        messages.success(
            request,
            f"Message sent from {sender.name} to {receiver.name}."
        )

        return redirect("dashboard")

    return redirect("dashboard")


# ==========================================
# 4. CREATE CHECKPOINT
# ==========================================

def create_checkpoint(request, process_id):

    process = get_object_or_404(Process, id=process_id)

    if process.status == "FAILED":

        messages.error(
            request,
            "Failed process cannot create checkpoint."
        )

        return redirect("dashboard")

    # Checkpoint label automatically generate
    count = process.checkpoints.count() + 1

    label = f"CP-{count}"

    checkpoint = Checkpoint.objects.create(
        process=process,
        label=label,
        state=process.state
    )

    Event.objects.create(
        event_type="CHECKPOINT_CREATED",
        description=(
            f"Checkpoint {checkpoint.label} created for "
            f"{process.name} with state {process.state}."
        )
    )

    messages.success(
        request,
        f"Checkpoint {label} created for {process.name}."
    )

    return redirect("dashboard")


# ==========================================
# 5. FAIL PROCESS
# ==========================================

def fail_process(request, process_id):

    process = get_object_or_404(Process, id=process_id)

    if process.status == "FAILED":

        messages.warning(
            request,
            f"{process.name} is already failed."
        )

        return redirect("dashboard")

    process.status = "FAILED"
    process.save()

    Event.objects.create(
        event_type="PROCESS_FAILED",
        description=f"Process {process.name} has failed."
    )

    messages.error(
        request,
        f"Process {process.name} failed."
    )

    return redirect("dashboard")


# ==========================================
# 6. ROLLBACK PROCESS
# ==========================================

@transaction.atomic
def rollback_process(request, process_id):

    process = get_object_or_404(
        Process.objects.select_for_update(),
        id=process_id
    )

    # Latest checkpoint find karo
    checkpoint = process.checkpoints.order_by("-id").first()

    if checkpoint is None:

        messages.error(
            request,
            f"No checkpoint found for {process.name}."
        )

        return redirect("dashboard")

    # Current state ko checkpoint state se replace karo
    old_state = process.state

    process.state = checkpoint.state
    process.status = "RUNNING"
    process.save()

    # ------------------------------------------
    # Messages rollback
    # ------------------------------------------

    # Is process ke latest checkpoint ke baad
    # bheje/receive kiye gaye messages identify karna
    #
    # Simple simulator ke liye hum latest checkpoint
    # ke state ko restore kar rahe hain.

    Event.objects.create(
        event_type="ROLLBACK",
        description=(
            f"{process.name} rolled back from state "
            f"{old_state} to {checkpoint.state} "
            f"using {checkpoint.label}."
        )
    )

    messages.success(
        request,
        (
            f"{process.name} rolled back successfully "
            f"to {checkpoint.label}."
        )
    )

    return redirect("dashboard")


# ==========================================
# 7. RESET PROCESS
# ==========================================

def reset_process(request, process_id):

    process = get_object_or_404(Process, id=process_id)

    process.state = 0
    process.status = "RUNNING"
    process.save()

    Event.objects.create(
        event_type="PROCESS_RESET",
        description=f"{process.name} reset to initial state."
    )

    messages.success(
        request,
        f"{process.name} has been reset."
    )

    return redirect("dashboard")