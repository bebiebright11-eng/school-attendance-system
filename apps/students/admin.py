from django.contrib import admin

from .models import Enrollment, Guardian, Student, StudentGuardian


class StudentGuardianInline(admin.TabularInline):
    model = StudentGuardian
    extra = 1
    fields = ('guardian', 'relationship', 'is_primary', 'can_pickup')


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    fields = ('academic_year', 'term', 'school_class', 'stream', 'date_enrolled', 'is_active')
    readonly_fields = ('date_enrolled',)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('admission_number', 'last_name', 'first_name', 'status', 'date_of_admission')
    list_filter = ('status',)
    search_fields = ('admission_number', 'first_name', 'last_name')
    ordering = ('last_name', 'first_name')
    readonly_fields = ('admission_number',)
    inlines = [StudentGuardianInline, EnrollmentInline]
    fieldsets = (
        ('Identity', {'fields': ('admission_number', 'first_name', 'last_name', 'date_of_birth', 'gender', 'photo')}),
        ('Enrollment', {'fields': ('date_of_admission', 'status')}),
        ('System Account', {'fields': ('user',)}),
    )


@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'phone_number', 'email', 'is_primary_contact')
    search_fields = ('first_name', 'last_name', 'phone_number', 'email')
    ordering = ('last_name', 'first_name')


@admin.register(StudentGuardian)
class StudentGuardianAdmin(admin.ModelAdmin):
    list_display = ('student', 'guardian', 'relationship', 'is_primary', 'can_pickup')
    list_filter = ('is_primary', 'can_pickup')
    search_fields = ('student__first_name', 'student__last_name', 'guardian__first_name', 'guardian__last_name')
    raw_id_fields = ('student', 'guardian')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'school_class', 'stream', 'academic_year', 'term', 'is_active')
    list_filter = ('academic_year', 'term', 'school_class', 'is_active')
    search_fields = ('student__first_name', 'student__last_name', 'student__admission_number')
    raw_id_fields = ('student',)
