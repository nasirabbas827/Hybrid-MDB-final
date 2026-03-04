from django.db import models
from django.utils import timezone


# =========================================================
# User Registration (Custom Table)
# =========================================================
class UserRegister(models.Model):

    ROLE_CHOICES = [
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.role})"


# =========================================================
# Dataset Upload (CSV / JSON Storage)
# =========================================================
class Dataset(models.Model):

    name = models.CharField(max_length=200)
    file = models.FileField(upload_to='datasets/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# =========================================================
# MDB Messages (Linked with Dataset)
# =========================================================
class MDBMessage(models.Model):

    content = models.TextField()

    posted_by = models.ForeignKey(
        UserRegister,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posted_messages'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.content[:50]


# =========================================================
# Keyword-Based Filtering
# =========================================================
class GlobalKeyword(models.Model):

    academic_keywords = models.CharField(max_length=5000)
    non_academic_keywords = models.CharField(max_length=5000)
    created_at = models.DateTimeField(auto_now_add=True)


# =========================================================
# Model Performance (Linked to Dataset)
# =========================================================
class ModelPerformance(models.Model):

    MODEL_TYPE_CHOICES = [
        ('logistic_regression', 'Logistic Regression'),
        ('naive_bayes', 'Naive Bayes'),
    ]

    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='model_performances'
    )

    model_type = models.CharField(max_length=50, choices=MODEL_TYPE_CHOICES)

    accuracy = models.FloatField()
    precision = models.FloatField()
    recall = models.FloatField()
    f1_score = models.FloatField()

    trained_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-trained_at']

    def __str__(self):
        return f"{self.model_type} - F1: {self.f1_score}"


# =========================================================
# Manual Review (Faculty Correction)
# =========================================================
class Review(models.Model):

    LABEL_CHOICES = [
        ('academic', 'Academic'),
        ('non_academic', 'Non Academic'),
    ]

    message = models.ForeignKey(
        MDBMessage,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    reviewer = models.ForeignKey(
        UserRegister,
        on_delete=models.CASCADE,
        related_name='reviews_done'
    )

    corrected_label = models.CharField(
        max_length=20,
        choices=LABEL_CHOICES
    )

    comment = models.TextField(null=True, blank=True)

    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-reviewed_at']

