from django.db import models
from django.contrib.auth.models import AbstractUser


# Üniversite modeli
class University(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Üniversite"
        verbose_name_plural = "Üniversiteler"

    def __str__(self):
        return self.name


# Geliştirilmiş kullanıcı modeli
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    university = models.ForeignKey(University, on_delete=models.SET_NULL, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = "Kullanıcı"
        verbose_name_plural = "Kullanıcılar"

    def __str__(self):
        return self.email


# Hedef modeli
class Goal(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    class Meta:
        verbose_name = "Hedef"
        verbose_name_plural = "Hedefler"

    def __str__(self):
        return self.name


# Alt hedef modeli
class SubGoal(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='subgoals')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    question_score = models.IntegerField("Soru Puanı", null=True, blank=True)
    is_numeric = models.BooleanField(default=False)  # Sayısal giriş gerektiriyor mu?
    requires_proof = models.BooleanField(default=False)  # Kanıt gerektirip gerektirmediğini belirleyen alan

    class Meta:
        verbose_name = "Alt Hedef"
        verbose_name_plural = "Alt Hedefler"

    def __str__(self):
        return self.name


# Seçenekler için yeni model
from django.db import models

class Option(models.Model):
    subgoal = models.ForeignKey(SubGoal, related_name='options', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)  # Seçeneğin adı
    value = models.IntegerField(null=True, blank=True)  # Seçeneğin değeri (örneğin 1-5)

    class Meta:
        verbose_name = "Seçenek"
        verbose_name_plural = "Seçenekler"

    def save(self, *args, **kwargs):
        # Eğer value değeri boşsa, otomatik olarak atanacak
        if not self.value:
            # Son eklenen seçeneğin value'sunu alıp +1 ekliyoruz
            last_option = Option.objects.filter(subgoal=self.subgoal).order_by('-value').first()
            if last_option:
                self.value = last_option.value + 1  # Bir önceki değerin üzerine 1 ekliyoruz
            else:
                self.value = 1  # Eğer hiçbir seçenek yoksa, değeri 1 olarak atıyoruz
        super(Option, self).save(*args, **kwargs)  # Bu satır, kaydın yapılmasını sağlar

    def __str__(self):
        return f"{self.subgoal.name} - {self.name} ({self.value})"


from django.core.validators import FileExtensionValidator


def user_proof_upload_path(instance, filename):
    return f'proofs/{instance.user.university}/AltHedef_{instance.subgoal.goal.name}/{filename}'


class SubGoalUserRating(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    subgoal = models.ForeignKey(SubGoal, on_delete=models.CASCADE)
    rating = models.IntegerField()
    pdf_upload = models.FileField(
        upload_to=user_proof_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        null=True,
        blank=True,
        verbose_name="Kanıt PDF"
    )
    total_score = models.FloatField(default=0)  # Kullanıcının aldığı puan
    total_max_score = models.FloatField(default=0)  # Maksimum puan

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'subgoal')
        verbose_name = "Alt Hedef Değerlendirmesi"
        verbose_name_plural = "Alt Hedef Değerlendirmeleri"

    def __str__(self):
        return f"{self.user.email} -> {self.subgoal.name}: {self.rating}"
