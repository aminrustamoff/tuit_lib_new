"""
=====================================================================
  ONLINE KUTUBXONA — FORMS
=====================================================================
  Formalar ro'yxati:
    Auth:
      RegisterForm        — ro'yxatdan o'tish
      LoginForm           — tizimga kirish

    Profil:
      ProfileEditForm     — profilni tahrirlash

    Kitob:
      BookForm            — admin: kitob qo'shish / tahrirlash

    Kategoriya:
      CategoryForm        — admin: kategoriya qo'shish / tahrirlash

    O'qituvchi ishlari:
      TeacherWorkForm     — qo'llanma / maqola yuklash

    Ariza:
      TeacherRequestForm  — o'qituvchilik maqomiga ariza

    Admin xabar:
      AdminMessageForm    — foydalanuvchiga xabar yuborish
=====================================================================
"""

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from .models import (
    User, Book, Category,
    TeacherWork, TeacherRequest, AdminMessage
)


# ─────────────────────────────────────────────────────────────────
#  AUTH FORMS
# ─────────────────────────────────────────────────────────────────

class RegisterForm(forms.ModelForm):
    """
    Ro'yxatdan o'tish formasi.
    Parol ikki marta kiritiladi va Django validatorlari orqali tekshiriladi.
    """
    password1 = forms.CharField(
        label="Parol",
        widget=forms.PasswordInput(attrs={
            'class':       'form-input',
            'placeholder': 'Parolni kiriting',
        }),
    )
    password2 = forms.CharField(
        label="Parolni tasdiqlang",
        widget=forms.PasswordInput(attrs={
            'class':       'form-input',
            'placeholder': 'Parolni qayta kiriting',
        }),
    )

    class Meta:
        model  = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username':   forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Foydalanuvchi nomi'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ism'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Familiya'}),
            'email':      forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email'}),
        }
        labels = {
            'username':   'Foydalanuvchi nomi',
            'first_name': 'Ism',
            'last_name':  'Familiya',
            'email':      'Email',
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Bu foydalanuvchi nomi band. Boshqasini tanlang.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("Bu email allaqachon ro'yxatdan o'tgan.")
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password:
            validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Parollar mos kelmadi.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """Tizimga kirish formasi."""
    username = forms.CharField(
        label="Foydalanuvchi nomi",
        widget=forms.TextInput(attrs={
            'class':       'form-input',
            'placeholder': 'Foydalanuvchi nomi',
            'autofocus':   True,
        }),
    )
    password = forms.CharField(
        label="Parol",
        widget=forms.PasswordInput(attrs={
            'class':       'form-input',
            'placeholder': 'Parol',
        }),
    )


# ─────────────────────────────────────────────────────────────────
#  PROFIL FORM
# ─────────────────────────────────────────────────────────────────

class ProfileEditForm(forms.ModelForm):
    """
    Profilni tahrirlash.
    Username va rol o'zgartirilmaydi — faqat shaxsiy ma'lumotlar.
    """
    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'bio', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ism'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Familiya'}),
            'email':      forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email'}),
            'phone':      forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+998 90 123 45 67'}),
            'bio':        forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'O\'zingiz haqingizda yozing...'}),
            'avatar':     forms.ClearableFileInput(attrs={'class': 'form-file'}),
        }
        labels = {
            'first_name': 'Ism',
            'last_name':  'Familiya',
            'email':      'Email',
            'phone':      'Telefon',
            'bio':        'Biografiya',
            'avatar':     'Profil rasmi',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # O'zidan boshqa user shu email ni ishlatayotganini tekshirish
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Bu email boshqa foydalanuvchiga tegishli.")
        return email


# ─────────────────────────────────────────────────────────────────
#  KITOB FORM
# ─────────────────────────────────────────────────────────────────

class BookForm(forms.ModelForm):
    """Admin: kitob qo'shish va tahrirlash."""
    class Meta:
        model  = Book
        fields = [
            'title', 'author', 'category',
            'cover_image', 'description',
            'published_date', 'file', 'is_active',
        ]
        widgets = {
            'title':          forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Kitob nomi'}),
            'author':         forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Muallif'}),
            'category':       forms.Select(attrs={'class': 'form-select'}),
            'description':    forms.Textarea(attrs={'class': 'form-textarea', 'rows': 5, 'placeholder': 'Kitob haqida qisqacha...'}),
            'published_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'cover_image':    forms.ClearableFileInput(attrs={'class': 'form-file'}),
            'file':           forms.ClearableFileInput(attrs={'class': 'form-file'}),
            'is_active':      forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
        labels = {
            'title':          'Kitob nomi',
            'author':         'Muallif',
            'category':       'Kategoriya',
            'description':    'Tavsif',
            'published_date': 'Nashr sanasi',
            'cover_image':    'Muqova rasmi',
            'file':           'Kitob fayli (PDF)',
            'is_active':      'Faol (saytda ko\'rinsin)',
        }

    def clean_published_date(self):
        date = self.cleaned_data.get('published_date')
        from django.utils.timezone import now
        if date and date > now().date():
            raise ValidationError("Nashr sanasi kelajakda bo'la olmaydi.")
        return date


# ─────────────────────────────────────────────────────────────────
#  KATEGORIYA FORM
# ─────────────────────────────────────────────────────────────────

class CategoryForm(forms.ModelForm):
    """Admin: kategoriya qo'shish va tahrirlash. Slug avtomatik hosil qilinadi."""
    class Meta:
        model  = Category
        fields = ['name', 'slug', 'description', 'icon']
        widgets = {
            'name':        forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Kategoriya nomi (masalan: IT)'}),
            'slug':        forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'url-slug (bo\'sh qoldirsangiz avtomatik)'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Qisqacha tavsif'}),
            'icon':        forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Emoji yoki CSS klass (📚 yoki fa-book)'}),
        }
        labels = {
            'name':        'Kategoriya nomi',
            'slug':        'Slug',
            'description': 'Tavsif',
            'icon':        'Ikonka',
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug', '').strip()
        name = self.cleaned_data.get('name', '')

        # Slug bo'sh bo'lsa nomdan avtomatik hosil qilish
        if not slug:
            slug = slugify(name)

        # Slug unikligini tekshirish (tahrirlashda o'zini istisno qilish)
        qs = Category.objects.filter(slug=slug)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Bu slug allaqachon mavjud.")

        return slug


# ─────────────────────────────────────────────────────────────────
#  O'QITUVCHI ISH FORM
# ─────────────────────────────────────────────────────────────────

class TeacherWorkForm(forms.ModelForm):
    """O'qituvchi: qo'llanma yoki maqola yuklash / tahrirlash."""
    class Meta:
        model  = TeacherWork
        fields = [
            'title', 'work_type', 'description',
            'file', 'cover_image', 'is_published',
        ]
        widgets = {
            'title':        forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Sarlavha'}),
            'work_type':    forms.Select(attrs={'class': 'form-select'}),
            'description':  forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'Qisqacha tavsif...'}),
            'file':         forms.ClearableFileInput(attrs={'class': 'form-file'}),
            'cover_image':  forms.ClearableFileInput(attrs={'class': 'form-file'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
        labels = {
            'title':        'Sarlavha',
            'work_type':    'Turi',
            'description':  'Tavsif',
            'file':         'Fayl (PDF, DOCX va h.k.)',
            'cover_image':  'Muqova rasmi',
            'is_published': 'Hoziroq e\'lon qilish',
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # 50 MB dan katta fayllarni qabul qilmaslik
            max_size = 50 * 1024 * 1024
            if file.size > max_size:
                raise ValidationError("Fayl hajmi 50 MB dan oshmasligi kerak.")
        return file


# ─────────────────────────────────────────────────────────────────
#  O'QITUVCHILIK ARIZASI FORM
# ─────────────────────────────────────────────────────────────────

class TeacherRequestForm(forms.ModelForm):
    """Talaba o'qituvchilik maqomiga ariza topshiradi."""
    class Meta:
        model  = TeacherRequest
        fields = ['motivation']
        widgets = {
            'motivation': forms.Textarea(attrs={
                'class':       'form-textarea',
                'rows':        6,
                'placeholder': (
                    "Nima uchun o'qituvchi maqomini olishni xohlaysiz?\n"
                    "Qanday yo'nalishda qo'llanma yoki maqola yozmoqchisiz?\n"
                    "Tajribangiz haqida qisqacha yozing..."
                ),
            }),
        }
        labels = {
            'motivation': 'Motivatsiya xati',
        }

    def clean_motivation(self):
        text = self.cleaned_data.get('motivation', '').strip()
        if len(text) < 50:
            raise ValidationError("Motivatsiya kamida 50 ta belgidan iborat bo'lishi kerak.")
        return text


# ─────────────────────────────────────────────────────────────────
#  ADMIN XABAR FORM
# ─────────────────────────────────────────────────────────────────

class AdminMessageForm(forms.ModelForm):
    """Admin foydalanuvchiga xabar yuboradi."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adminlar o'ziga xabar yubora olmaydi
        self.fields['recipient'].queryset = User.objects.exclude(
            role=User.Role.ADMIN
        ).order_by('username')
        self.fields['recipient'].label_from_instance = lambda u: (
            f"{u.get_full_name() or u.username} ({u.get_role_display()})"
        )

    class Meta:
        model  = AdminMessage
        fields = ['recipient', 'subject', 'body']
        widgets = {
            'recipient': forms.Select(attrs={'class': 'form-select'}),
            'subject':   forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Xabar mavzusi'}),
            'body':      forms.Textarea(attrs={'class': 'form-textarea', 'rows': 6, 'placeholder': 'Xabar matni...'}),
        }
        labels = {
            'recipient': 'Qabul qiluvchi',
            'subject':   'Mavzu',
            'body':      'Xabar matni',
        }

    def clean_subject(self):
        subject = self.cleaned_data.get('subject', '').strip()
        if len(subject) < 3:
            raise ValidationError("Mavzu kamida 3 ta belgidan iborat bo'lishi kerak.")
        return subject

    def clean_body(self):
        body = self.cleaned_data.get('body', '').strip()
        if len(body) < 10:
            raise ValidationError("Xabar matni kamida 10 ta belgidan iborat bo'lishi kerak.")
        return body