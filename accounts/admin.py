from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, University, Goal, SubGoal, SubGoalUserRating, Option


# Admin başlıklarını Türkçeleştiriyoruz
class CustomAdminSite(admin.AdminSite):
    site_header = "Yönetim Paneli"
    site_title = "Admin"
    index_title = "Kontrol Paneli"

    class Media:
        css = {
            'all': ('css/admin.css',)  # Özel admin CSS'inizi burada tanımlayın
        }


# Global admin.site nesnesini CustomAdminSite ile değiştiriyoruz
admin.site.__class__ = CustomAdminSite


# Option için inline yapı
class OptionInline(admin.TabularInline):
    model = Option
    extra = 5  # Varsayılan olarak 1 seçenek eklenmesi sağlanacak
    fields = ['name', 'value']
    readonly_fields = ['value']  # Alanlar yalnızca okunabilir


# SubGoal için inline yapı
class SubGoalInline(admin.TabularInline):
    model = SubGoal
    extra = 0


# SubGoalUserRating inline
class SubGoalUserRatingInline(admin.TabularInline):
    model = SubGoalUserRating
    extra = 0


# CustomUser admin
@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    list_display = ('email', 'username', 'first_name', 'last_name', 'university', 'is_staff')
    list_filter = ('university', 'is_staff', 'is_superuser')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    inlines = [SubGoalUserRatingInline]
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Üniversite Bilgisi', {'fields': ('university',)}),
    )


# University admin
@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


# Goal admin
@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    inlines = [SubGoalInline]


# SubGoal admin
@admin.register(SubGoal)
class SubGoalAdmin(admin.ModelAdmin):
    list_display = ('name', 'goal', 'question_score')
    list_filter = ('goal', 'is_numeric')
    search_fields = ('name', 'goal__name')
    autocomplete_fields = ['goal']
    inlines = [OptionInline]  # SubGoal ile ilişkili seçeneklerin görünmesi için inline ekledik


# Özel admin action
@admin.action(description='Tüm puanları sıfırla')
def reset_ratings(modeladmin, request, queryset):
    queryset.update(rating=None)


@admin.register(SubGoalUserRating)
class SubGoalUserRatingAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'goal_name', 'subgoal_name', 'total_score','total_max_score','rating', 'updated_at')  # 'goal_name' da eklendi
    list_filter = ('rating', 'updated_at')
    search_fields = ('user__email', 'subgoal__name', 'subgoal__goal__name')  # Goal adını arama alanına da ekliyoruz
    autocomplete_fields = ['user', 'subgoal']
    actions = [reset_ratings]

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = 'Kullanıcı E-Posta'

    def subgoal_name(self, obj):
        return obj.subgoal.name

    subgoal_name.short_description = 'Alt Hedef'

    def goal_name(self, obj):
        return obj.subgoal.goal.name  # SubGoal üzerinden Goal adını alıyoruz

    goal_name.short_description = 'Ana Hedef'
