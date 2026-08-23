from django.contrib import admin

from .models import AcademicYear, Classroom, Class, Department, Stream, Term


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current',)
    search_fields = ('name',)
    ordering = ('-start_date',)


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'term_number', 'start_date', 'end_date', 'is_current')
    list_filter = ('academic_year', 'is_current')
    search_fields = ('name', 'academic_year__name')
    ordering = ('academic_year', 'term_number')


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'level')
    search_fields = ('name',)
    ordering = ('level',)


@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ('name', 'school_class')
    list_filter = ('school_class',)
    search_fields = ('name', 'school_class__name')
    ordering = ('school_class', 'name')


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'head')
    search_fields = ('name',)
    ordering = ('name',)
    raw_id_fields = ('head',)
