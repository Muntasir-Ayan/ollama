from django.db import models

class Hotel(models.Model):
    # Fields as before
    original_id = models.IntegerField(unique=True)
    original_title = models.CharField(max_length=255)
    rewritten_title = models.CharField(max_length=255)
    short_description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Hotels'  # Explicitly use the correct table name with quotes to preserve case

    def __str__(self):
        return f"{self.original_title} - {self.rewritten_title}"
