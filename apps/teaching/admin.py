from django.contrib import admin

from .models import ClassParentAssignment, Subject, Teacher, TeachingAssignment


class TeachingAssignmentInline(admin.TabularInline):
    model = TeachingAssignment
    extra = 0
    fields = ('subject', 'school_class', 'stream', 'academic_year')


class ClassParentAssignmentInline(admin.TabularInline):
    model = ClassParentAssignment
    extra = 0
    fields = ('school_class', 'stream', 'academic_year', 'is_active')


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('employee_number', 'get_full_name', 'phone_number')
    search_fields = ('employee_number', 'user__first_name', 'user__last_name', 'user__email')
    ordering = ('employee_number',)
    inlines = [TeachingAssignmentInline, ClassParentAssignmentInline]
    fieldsets = (
        ('Identity', {'fields': ('employee_number', 'qualification', 'phone_number')}),
        ('System Account', {'fields': ('user',)}),
    )

    @admin.display(description='Full Name')
    def get_full_name(self, obj):
        return obj.get_full_name()


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')
    ordering = ('name',)


@admin.register(TeachingAssignment)
class TeachingAssignmentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'subject', 'school_class', 'stream', 'academic_year')
    list_filter = ('academic_year', 'school_class')
    search_fields = ('teacher__employee_number', 'teacher__user__first_name', 'teacher__user__last_name', 'subject__name')
    raw_id_fields = ('teacher',)


@admin.register(ClassParentAssignment)
class ClassParentAssignmentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'school_class', 'stream', 'academic_year', 'is_active')
    list_filter = ('academic_year', 'school_class', 'is_active')
    search_fields = ('teacher__employee_number', 'teacher__user__first_name', 'teacher__user__last_name', 'school_class__name')
    raw_id_fields = ('teacher',)
