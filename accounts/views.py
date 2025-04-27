import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter, landscape
from .forms import RegistrationForm, SubGoalUserRatingForm
from .models import CustomUser, Goal, SubGoal, SubGoalUserRating, Option


def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        try:
            user = CustomUser.objects.get(email=email)
            user = authenticate(request, username=user.email, password=password)
            if user:
                login(request, user)
                return redirect('home')
            messages.error(request, 'Geçersiz e-posta veya şifre.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'Bu e-posta ile kayıtlı kullanıcı bulunamadı.')

    return render(request, 'accounts/login.html')


def register_view(request):
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Kaydınız başarıyla tamamlandı!')
            return redirect('login')

    return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


def home_view(request):
    user = request.user
    university = user.university
    goals = Goal.objects.all()
    goal_stats = {}

    for goal in goals:
        subgoals = goal.subgoals.all()
        stats = {
            'total_questions': subgoals.count(),
            'answered_questions': 0,
            'expected_score': 0,
            'total_score': 0,  # Buradaki toplam puanı güncelleyeceğiz
            'subgoal_scores': {},
            'completion_percentage': 0,
        }

        for subgoal in subgoals:
            rating = SubGoalUserRating.objects.filter(user=user, subgoal=subgoal).first()
            score = 0

            # Puan hesaplaması
            if subgoal.question_score is not None:
                stats['total_score'] += subgoal.question_score  # Burada sadece soru puanı ekliyoruz
            else:
                # Puanı yoksa, 0 olarak kabul ediyoruz
                stats['total_score'] += 0  # Alt hedefin puanı yoksa 0

            if rating and rating.rating and subgoal.question_score is not None:
                stats['answered_questions'] += 1
                # Seçenek sayısına göre beklenen puan hesaplama
                option_count = subgoal.options.count()  # Seçenek sayısını alıyoruz
                if option_count > 0:
                    score = (rating.rating / option_count) * subgoal.question_score
                stats['expected_score'] += score  # Beklenen puan

            # Puanı yoksa yine 1 olarak kabul edip hesaplama yapılmasını sağlıyoruz
            if subgoal.question_score is None:
                stats['answered_questions'] += 1  # Puanı olmayan alt hedefleri de sayıyoruz

            stats['subgoal_scores'][subgoal.id] = round(score, 2)

        if stats['total_questions'] > 0:
            stats['completion_percentage'] = round((stats['answered_questions'] / stats['total_questions']) * 100, 2)

        stats['expected_score'] = round(stats['expected_score'], 2)
        goal_stats[goal.id] = stats

    if request.GET.get('download_pdf'):
        return create_pdf(user, goal_stats)

    return render(request, 'home.html', {
        'goals': goals,
        'university': university,
        'goal_stats': goal_stats
    })


def goal_detail(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id)
    return render(request, 'goal_detail.html', {'goal': goal})


def subgoal_list_view(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id)
    subgoals = goal.subgoals.all()

    user_selections = {}
    user_scores = {}
    total_score = 0
    pdf_files = {}
    total_max_score = 0  # Tüm soruların toplam puanı

    for subgoal in subgoals:
        rating = SubGoalUserRating.objects.filter(user=request.user, subgoal=subgoal).first()
        selected_option = None
        if rating:
            selected_option = Option.objects.filter(subgoal=subgoal, value=rating.rating).first()
        user_selections[subgoal.id] = selected_option

        score = 0
        if rating and rating.rating and subgoal.question_score is not None:
            try:
                # Seçenek sayısına göre puan hesaplama
                option_count = subgoal.options.count()  # Seçenek sayısını alıyoruz
                score = (rating.rating / option_count) * subgoal.question_score
            except Exception as e:
                print(f"Puan hesaplama hatası: {e}")
        else:
            # Eğer alt hedefin puanı yoksa, 0 olarak kabul et
            score = 0  # Alt hedefin puanı yoksa 0 olarak kabul ediyoruz

        user_scores[subgoal.id] = score
        total_score += score
        total_max_score += subgoal.question_score  # Maksimum toplam puanı artırıyoruz

        # PDF dosyası varsa ekle
        if rating and rating.pdf_upload:
            pdf_files[subgoal.id] = rating.pdf_upload.url

        if rating:
            rating.total_score = score  # Kullanıcının aldığı puanı kaydediyoruz
            rating.total_max_score = subgoal.question_score  # Maksimum puanı kaydediyoruz
            rating.save()  # Güncellenmiş veriyi kaydediyoruz

        # Eğer puanı yoksa, sadece soru sayısını dahil ediyoruz
        if subgoal.question_score is None:
            total_score += 0  # Eğer puan yoksa, 0 ekleyerek ilerliyoruz

    return render(request, 'subgoal_list.html', {
        'goal': goal,
        'subgoals': subgoals,
        'user_selections': user_selections,
        'user_scores': user_scores,
        'total_score': total_score,
        'total_max_score': total_max_score,  # Tüm soruların toplam puanı
        'pdf_files': pdf_files,

    })


def save_subgoal_rating(request, subgoal_id):
    subgoal = get_object_or_404(SubGoal, id=subgoal_id)
    if request.method == 'POST':

        form = SubGoalUserRatingForm(request.POST, request.FILES, subgoal=subgoal)
        if form.is_valid():
            rating_value = int(form.cleaned_data['rating'])
            pdf_file = form.cleaned_data.get('pdf_upload')

            SubGoalUserRating.objects.update_or_create(
                user=request.user,
                subgoal=subgoal,
                defaults={'rating': rating_value, 'pdf_upload': pdf_file}
            )
            messages.success(request, 'Cevabınız kaydedildi!')
        else:
            messages.error(request, 'Cevabınız kaydedilirken bir hata oluştu.')

        # Kullanıcıyı ilgili alt hedefin olduğu sayfaya yönlendiriyoruz
        goal_id = subgoal.goal.id
        return redirect(f"{reverse('subgoal_list', args=[goal_id])}#subgoal-{subgoal.id}")


def create_pdf(user, goal_stats):
    # Font kaydını yap
    font_path = os.path.join('static', 'fonts', 'DejaVuSans.ttf')

    # Eğer font dosyası mevcutsa kaydet
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('DejaVu', font_path))
    else:
        raise FileNotFoundError(f"Font dosyası bulunamadı: {font_path}")

    # PDF dosya adı ve HTTP yanıtı oluştur
    file_name = f"{user.first_name}_{user.last_name}_report.pdf"
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename={file_name}'
    doc = SimpleDocTemplate(response, pagesize=landscape(letter))  # Yatay sayfa yönü

    # Stil ayarları
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Turkish', fontName='DejaVu', fontSize=12, spaceAfter=10))
    styles.add(
        ParagraphStyle(name='TurkishHeading', fontName='DejaVu', fontSize=20, spaceAfter=20, alignment=1, leading=24))
    styles.add(
        ParagraphStyle(name='UserInfo', fontName='DejaVu', fontSize=14, spaceAfter=15, alignment=0, leftIndent=20))
    styles['Heading1'].fontName = 'DejaVu'

    # İçerik listesi
    content = []

    # Başlık ekle
    content.append(Paragraph("Kullanıcı Raporu", styles['TurkishHeading']))

    # Kullanıcı bilgilerini direkt paragraf olarak ekle
    content.append(Paragraph(f"<b>Ad:</b> {user.first_name}", styles['UserInfo']))
    content.append(Paragraph(f"<b>Soyad:</b> {user.last_name}", styles['UserInfo']))
    content.append(Paragraph(f"<b>E-posta:</b> {user.email}", styles['UserInfo']))
    content.append(Paragraph(f"<b>Üniversite:</b> {user.university.name if user.university else 'Bilinmiyor'}",
                             styles['UserInfo']))
    content.append(PageBreak())  # Kullanıcı bilgileri sonrası yeni sayfaya geç
    # Her hedef için rapor oluştur
    for goal_id, stats in goal_stats.items():
        goal = Goal.objects.get(id=goal_id)
        content.append(Paragraph(f"HEDEF: {goal.name}", styles['Heading1']))

        # Alt hedefler ve puanları tablosu
        goal_data = [["Alt Hedef", "Puan"]]
        subgoal_scores = stats.get('subgoal_scores', {})

        for subgoal in goal.subgoals.all():
            score = subgoal_scores.get(subgoal.id, 0)
            goal_data.append([subgoal.name, str(int(score))])  # Puanı tam sayıya çevir

        goal_table = create_table(goal_data)
        content.append(goal_table)
        content.append(PageBreak())  # Hedef tablosu sonrası yeni sayfaya geç

    # PDF'yi oluştur
    doc.build(content)
    return response


def create_table(data):
    """
    Tabloyu oluşturmak için yardımcı fonksiyon.
    """
    # Burada sütun genişliklerini esnek yapıyoruz. Bunu ihtiyacınıza göre ayarlayabilirsiniz.
    # Eğer çok uzun metinler varsa, belirli bir uzunluktan sonra kırılma uygulayabiliriz
    for row in range(1, len(data)):
        for col in range(len(data[row])):
            # Eğer metin 100 karakterden uzunsa, sarmalansın
            if len(data[row][col]) > 100:
                data[row][col] = data[row][col][:100] + "..."  # Sadece ilk 100 karakteri al ve sonuna "..." ekle
    table = Table(data, colWidths=[600, None])  # 2. sütun genişliği ayarlandı, 150px

    # Kelime sarmalama (wordwrap) ile metni düzgün şekilde sarmalı
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.dimgray),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVu'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 5),  # Üst padding'i ayarlayın
        ('LEFTPADDING', (0, 0), (-1, -1), 5),  # Sol padding'i ayarlayın
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),  # Sağ padding'i ayarlayın
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('WORDWRAP', (0, 0), (-1, -1), True),  # Kelime sarmalama aktif
        ('FONTSIZE', (0, 0), (-1, -1), 11),  # Yazı tipi boyutunu küçült
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Puanları sağa hizala
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Hücrelerin dikey hizalanması
        ('LINEBEFORE', (0, 0), (0, -1), 0.5, colors.black),  # Sol sınır çizgisi
        ('LINEAFTER', (1, 0), (1, -1), 0.5, colors.black),  # Sağ sınır çizgisi
    ]))

    return table
