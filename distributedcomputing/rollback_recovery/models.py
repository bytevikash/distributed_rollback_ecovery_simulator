from django.db import models


class Process(models.Model):
    STATUS_CHOICES = [
        ("RUNNING", "Running"),
        ("FAILED", "Failed"),
    ]

    name = models.CharField(max_length=20, unique=True)
    state = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="RUNNING")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class Message(models.Model):
    sender = models.ForeignKey(
        Process, on_delete=models.CASCADE, related_name="sent_messages"
    )
    receiver = models.ForeignKey(
        Process, on_delete=models.CASCADE, related_name="received_messages"
    )
    data = models.CharField(max_length=255)
    amount = models.IntegerField(default=10)
    delivered = models.BooleanField(default=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.sender.name} -> {self.receiver.name}: {self.data}"


class Checkpoint(models.Model):
    process = models.ForeignKey(
        Process, on_delete=models.CASCADE, related_name="checkpoints"
    )
    label = models.CharField(max_length=30)
    state = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["process_id", "id"]

    def __str__(self):
        return f"{self.process.name} - {self.label}"


class Event(models.Model):
    event_type = models.CharField(max_length=30)
    description = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.description