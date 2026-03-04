from django.contrib import admin
from django.contrib import messages

from .models import (
    UserRegister,
    Dataset,
    MDBMessage,
    GlobalKeyword,
    ModelPerformance,
    Review
)

from .train_models import train_models_from_dataset


# =====================================
# Custom Action for Training
# =====================================
@admin.action(description="Train AI Models (LR + NB)")
def train_ai_models(modeladmin, request, queryset):
    for dataset in queryset:
        try:
            # Updated: only pass dataset (no request.user)
            train_models_from_dataset(dataset)

            messages.success(
                request,
                f"Models trained successfully for dataset: {dataset.name}"
            )
        except Exception as e:
            messages.error(
                request,
                f"Error training dataset {dataset.name}: {str(e)}"
            )


# =====================================
# Dataset Admin
# =====================================
@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "uploaded_at")
    search_fields = ("name",)
    ordering = ("-uploaded_at",)
    actions = [train_ai_models]


# =====================================
# ModelPerformance Admin
# =====================================
@admin.register(ModelPerformance)
class ModelPerformanceAdmin(admin.ModelAdmin):
    list_display = (
        "dataset",
        "model_type",
        "accuracy",
        "precision",
        "recall",
        "f1_score",
        "trained_at",
    )
    list_filter = ("model_type", "trained_at")
    search_fields = ("dataset__name",)
    ordering = ("-trained_at",)


# =====================================
# MDBMessage Admin
# =====================================
@admin.register(MDBMessage)
class MDBMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "short_content", "posted_by", "created_at")
    list_filter = ("posted_by", "created_at")
    search_fields = ("content",)
    ordering = ("-created_at",)

    def short_content(self, obj):
        return obj.content[:50]
    short_content.short_description = "Message"


# =====================================
# Keyword Admin
# =====================================
admin.site.register(GlobalKeyword)


# =====================================
# Review Admin
# =====================================
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("message", "reviewer", "corrected_label", "reviewed_at")
    list_filter = ("corrected_label", "reviewed_at")
    search_fields = ("message__content", "reviewer__full_name")
    ordering = ("-reviewed_at",)


# =====================================
# UserRegister Admin
# =====================================
@admin.register(UserRegister)
class UserRegisterAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "email",
        "role",
        "status",
        "created_at",
    )
    list_filter = ("role", "status", "gender", "country")
    search_fields = ("full_name", "email", "phone")
    ordering = ("-created_at",)