from django.contrib import admin

from .models import AcademicYear, Class, Stream, Term


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current',)
    search_fields = ('name',)
    ordering = ('-start_date',)


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'term_number', 'start_date', 'end_date')
    list_filter = ('academic_year',)
    search_fields = ('name', 'academic_year__name')
    ordering = ('academic_year', 'term_number')


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'capacity')
    search_fields = ('name',)
    ordering = ('level',)


@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ('name', 'school_class')
    list_filter = ('school_class',)
    search_fields = ('name', 'school_class__name')
    ordering = ('school_class', 'name')
