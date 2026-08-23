from django.contrib import admin

from .models import ClassParentAssignment, Lesson, Subject, Teacher, TeacherAssignment


class TeacherAssignmentInline(admin.TabularInline):
    model = TeacherAssignment
    extra = 0
    fields = ('subject', 'school_class', 'stream', 'academic_year', 'is_active')


class ClassParentAssignmentInline(admin.TabularInline):
    model = ClassParentAssignment
    extra = 0
    fields = ('school_class', 'stream', 'academic_year', 'is_active')


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('employee_number', 'last_name', 'first_name', 'department', 'is_active')
    list_filter = ('department', 'is_active')
    search_fields = ('employee_number', 'first_name', 'last_name', 'email')
    ordering = ('last_name', 'first_name')
    inlines = [TeacherAssignmentInline, ClassParentAssignmentInline]
    fieldsets = (
        ('Identity', {'fields': ('employee_number', 'first_name', 'last_name')}),
        ('Contact', {'fields': ('phone_number', 'email')}),
        ('School', {'fields': ('department', 'date_joined', 'is_active')}),
        ('System Account', {'fields': ('user',)}),
    )


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'department', 'is_active')
    list_filter = ('department', 'is_active')
    search_fields = ('name', 'code')
    ordering = ('name',)


@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'subject', 'school_class', 'stream', 'academic_year', 'is_active')
    list_filter = ('academic_year', 'school_class', 'is_active')
    search_fields = ('teacher__first_name', 'teacher__last_name', 'subject__name')
    raw_id_fields = ('teacher',)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'term', 'day_of_week', 'start_time', 'end_time', 'classroom', 'is_active')
    list_filter = ('term', 'day_of_week', 'is_active')
    search_fields = ('assignment__subject__name', 'assignment__teacher__last_name', 'classroom__name')


@admin.register(ClassParentAssignment)
class ClassParentAssignmentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'school_class', 'stream', 'academic_year', 'is_active')
    list_filter = ('academic_year', 'school_class', 'is_active')
    search_fields = ('teacher__first_name', 'teacher__last_name', 'school_class__name')
    raw_id_fields = ('teacher',)
