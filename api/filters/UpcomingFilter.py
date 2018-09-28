from datetime import date, datetime
from django.contrib import admin


class DateListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'Date'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'date'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('upcoming', 'Upcoming'),
            ('previous', 'Previous'),
            ('all', 'All'),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        today = datetime.today()

        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value() == 'upcoming' or self.value() is None:
            return queryset.filter(net__gte=date(today.year, today.month, today.day)).order_by('net')
        if self.value() == 'previous':
            return queryset.filter(net__lte=date(today.year, today.month, today.day)).order_by('-net')
        if self.value() == 'all':
            return queryset.order_by('net')
