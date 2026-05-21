from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


# ─────────────────────────────────────────────
#  FOYDALANUVCHI MODELI
# ─────────────────────────────────────────────

class User(AbstractUser):
    """
    Asosiy foydalanuvchi modeli.
    Har bir foydalanuvchi ro'yxatdan o'tganda 'student' roli bilan boshlanadi.
    """

    class Role(models.TextChoices):
        STUDENT = 'student', 'Talaba'
        TEACHER = 'teacher', "O'qituvchi"
        ADMIN   = 'admin',   'Admin'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT,
        verbose_name="Rol",
    )
    avatar = models.ImageField(
        upload_to='media/avatars/',
        null=True,
        blank=True,
        verbose_name="Profil rasmi",
    )
    bio = models.TextField(
        blank=True,
        verbose_name="Biografiya",
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Telefon raqami",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        verbose_name='user permissions',
    )

    def is_student(self):
        return self.role == self.Role.STUDENT

    def is_teacher(self):
        return self.role == self.Role.TEACHER

    def is_admin(self):
        return self.role == self.Role.ADMIN

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# ─────────────────────────────────────────────
#  O'QITUVCHILIK ARIZASI
# ─────────────────────────────────────────────

class TeacherRequest(models.Model):
    """
    Talaba o'qituvchilik maqomiga ariza tashlaydi.
    Admin panel orqali tasdiqlash yoki rad etish mumkin.
    """

    class Status(models.TextChoices):
        PENDING  = 'pending',  'Kutilmoqda'
        APPROVED = 'approved', 'Tasdiqlandi'
        REJECTED = 'rejected', 'Rad etildi'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_requests',
        verbose_name="Ariza beruvchi",
    )
    motivation = models.TextField(
        verbose_name="Motivatsiya (ariza matni)",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Holat",
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_requests',
        verbose_name="Ko'rib chiqqan admin",
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Ko'rib chiqilgan sana",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "O'qituvchilik arizasi"
        verbose_name_plural = "O'qituvchilik arizalari"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} → {self.get_status_display()}"


# ─────────────────────────────────────────────
#  KITOB KATEGORIYASI
# ─────────────────────────────────────────────

class Category(models.Model):
    """
    Kitob kategoriyalari: IT, Literature, Science va h.k.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Kategoriya nomi",
    )
    slug = models.SlugField(
        unique=True,
        verbose_name="Slug (URL uchun)",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Tavsif",
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Ikonka (emoji yoki CSS klass)",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        ordering = ['name']

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────
#  KITOB MODELI
# ─────────────────────────────────────────────

class Book(models.Model):
    """
    Kutubxonadagi asosiy kitob modeli.
    """
    title = models.CharField(
        max_length=255,
        verbose_name="Kitob nomi",
    )
    author = models.CharField(
        max_length=255,
        verbose_name="Muallif",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='books',
        verbose_name="Kategoriya",
    )
    cover_image = models.ImageField(
        upload_to='media/book_covers/',
        null=True,
        blank=True,
        verbose_name="Muqova rasmi",
    )
    description = models.TextField(
        verbose_name="Qisqacha tavsif",
    )
    published_date = models.DateField(
        verbose_name="Nashr sanasi",
    )
    file = models.FileField(
        upload_to='media/books/',
        null=True,
        blank=True,
        verbose_name="Kitob fayli (PDF va h.k.)",
    )
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='added_books',
        verbose_name="Kim qo'shgan",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Faolmi?",
    )
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Ko'rishlar soni",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kitob"
        verbose_name_plural = "Kitoblar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.author}"


# ─────────────────────────────────────────────
#  TALABANING SAQLAB QOLGAN KITOBLARI
# ─────────────────────────────────────────────

class SavedBook(models.Model):
    """
    Talaba o'zining profiliga kitob qo'shganda shu model ishlatiladi.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_books',
        verbose_name="Foydalanuvchi",
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='saved_by',
        verbose_name="Kitob",
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Saqlangan kitob"
        verbose_name_plural = "Saqlangan kitoblar"
        unique_together = ('user', 'book')   # bir kitobni ikki marta saqlash mumkin emas
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.user.username} → {self.book.title}"


# ─────────────────────────────────────────────
#  O'QITUVCHI ISHLARI (qo'llanma / maqola)
# ─────────────────────────────────────────────

class TeacherWork(models.Model):
    """
    Faqat o'qituvchi roli bo'lgan foydalanuvchilar
    o'z qo'llanma va maqolalarini shu model orqali yuklaydi.
    """

    class WorkType(models.TextChoices):
        GUIDE   = 'guide',   "Qo'llanma"
        ARTICLE = 'article', 'Maqola'
        OTHER   = 'other',   'Boshqa'

    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='works',
        verbose_name="O'qituvchi",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Sarlavha",
    )
    work_type = models.CharField(
        max_length=10,
        choices=WorkType.choices,
        default=WorkType.GUIDE,
        verbose_name="Turi",
    )
    description = models.TextField(
        verbose_name="Qisqacha tavsif",
    )
    file = models.FileField(
        upload_to='media/teacher_works/',
        verbose_name="Fayl",
    )
    cover_image = models.ImageField(
        upload_to='media/work_covers/',
        null=True,
        blank=True,
        verbose_name="Muqova rasmi",
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name="Chop etilganmi?",
    )
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Ko'rishlar soni",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "O'qituvchi ishi"
        verbose_name_plural = "O'qituvchi ishlari"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.teacher.username}: {self.title}"


# ─────────────────────────────────────────────
#  ADMIN → FOYDALANUVCHI XABARLARI
# ─────────────────────────────────────────────

class AdminMessage(models.Model):
    """
    Admin paneldan talaba yoki o'qituvchiga xabar yuborish.
    """
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name="Jo'natuvchi (admin)",
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages',
        verbose_name="Qabul qiluvchi",
    )
    subject = models.CharField(
        max_length=255,
        verbose_name="Mavzu",
    )
    body = models.TextField(
        verbose_name="Xabar matni",
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name="O'qilganmi?",
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="O'qilgan vaqt",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Admin xabari"
        verbose_name_plural = "Admin xabarlari"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender.username} → {self.recipient.username}: {self.subject}"


# ─────────────────────────────────────────────
#  SAYT STATISTIKASI (Home page uchun)
# ─────────────────────────────────────────────

class SiteStatistics(models.Model):
    """
    Home page da ko'rsatiladigan umumiy statistika.
    Har kuni yoki har soat yangilanishi mumkin (signal yoki task orqali).
    """
    total_books    = models.PositiveIntegerField(default=0, verbose_name="Jami kitoblar")
    total_users    = models.PositiveIntegerField(default=0, verbose_name="Jami foydalanuvchilar")
    total_teachers = models.PositiveIntegerField(default=0, verbose_name="Jami o'qituvchilar")
    total_works    = models.PositiveIntegerField(default=0, verbose_name="Jami o'qituvchi ishlari")
    updated_at     = models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqt")

    class Meta:
        verbose_name = "Sayt statistikasi"
        verbose_name_plural = "Sayt statistikasi"

    def __str__(self):
        return f"Statistika ({self.updated_at.strftime('%Y-%m-%d %H:%M')})"