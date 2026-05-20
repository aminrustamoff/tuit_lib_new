"""
=====================================================================
  ONLINE KUTUBXONA — VIEWS
=====================================================================
  Rol asosida himoya:
    @login_required          — faqat login bo'lganlar
    @role_required('teacher') — faqat o'qituvchilar
    @role_required('admin')   — faqat adminlar

  Mixinlar:
    LoginRequiredMixin  — class-based viewlar uchun
    TeacherRequiredMixin
    AdminRequiredMixin
=====================================================================
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.utils import timezone
from django.http import HttpResponseForbidden

from .services.run_ai_prompt import run_ai_prompt
import json


from .models import (
    User, Book, Category, SavedBook,
    TeacherWork, TeacherRequest, AdminMessage, SiteStatistics
)
from .forms import (
    RegisterForm, LoginForm, ProfileEditForm,
    BookForm, CategoryForm, TeacherWorkForm,
    TeacherRequestForm, AdminMessageForm
)


# ─────────────────────────────────────────────────────────────────
#  YORDAMCHI MIXINLAR
# ─────────────────────────────────────────────────────────────────

class TeacherRequiredMixin(LoginRequiredMixin):
    """Faqat o'qituvchi yoki admin kira oladi."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role not in (User.Role.TEACHER, User.Role.ADMIN):
            return HttpResponseForbidden("Bu sahifa faqat o'qituvchilar uchun.")
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(LoginRequiredMixin):
    """Faqat admin kira oladi."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role != User.Role.ADMIN:
            return HttpResponseForbidden("Bu sahifa faqat adminlar uchun.")
        return super().dispatch(request, *args, **kwargs)


# ─────────────────────────────────────────────────────────────────
#  PUBLIC VIEWS
# ─────────────────────────────────────────────────────────────────

class HomeView(View):
    """
    Home page:
      - Sayt statistikasi
      - So'nggi kitoblar
      - Registratsiya bo'limi (login bo'lmagan userlar uchun)
    """
    template_name = 'main/home.html'

    def get(self, request):
        stats      = SiteStatistics.objects.last()
        new_books  = Book.objects.filter(is_active=True).order_by('-created_at')[:8]
        categories = Category.objects.all()

        context = {
            'stats':      stats,
            'new_books':  new_books,
            'categories': categories,
        }
        return render(request, self.template_name, context)


class BookListView(View):
    """
    Barcha kitoblar ro'yxati.
    Qidiruv (q) va kategoriya filtri (category) qo'llab-quvvatlanadi.
    """
    template_name = 'main/book_list.html'

    def get(self, request):
        queryset   = Book.objects.filter(is_active=True).select_related('category')
        query      = request.GET.get('q', '').strip()
        cat_slug   = request.GET.get('category', '').strip()
        categories = Category.objects.all()

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(author__icontains=query) |
                Q(description__icontains=query)
            )

        if cat_slug:
            queryset = queryset.filter(category__slug=cat_slug)

        context = {
            'books':            queryset,
            'categories':       categories,
            'current_query':    query,
            'current_category': cat_slug,
        }
        return render(request, self.template_name, context)


class BookDetailView(View):
    """
    Bitta kitob sahifasi. Ko'rishlar sonini oshiradi.
    Login bo'lgan user uchun "Saqlangan?" belgisi ham ko'rsatiladi.
    """
    template_name = 'main/book_detail.html'

    def get(self, request, pk):
        book = get_object_or_404(Book, pk=pk, is_active=True)

        # Ko'rishlar sonini oshirish
        Book.objects.filter(pk=pk).update(view_count=book.view_count + 1)

        is_saved = False
        if request.user.is_authenticated:
            is_saved = SavedBook.objects.filter(user=request.user, book=book).exists()

        context = {
            'book':     book,
            'is_saved': is_saved,
        }
        return render(request, self.template_name, context)


class CategoryBooksView(View):
    """Kategoriya bo'yicha filtrlangan kitoblar."""
    template_name = 'main/category_books.html'

    def get(self, request, slug):
        category = get_object_or_404(Category, slug=slug)
        books    = Book.objects.filter(category=category, is_active=True)
        context  = {'category': category, 'books': books}
        return render(request, self.template_name, context)


class TeacherWorkListView(View):
    """O'qituvchilarning barcha ishlari (umumiy ro'yxat)."""
    template_name = 'main/work_list.html'

    def get(self, request):
        works      = TeacherWork.objects.filter(is_published=True).select_related('teacher')
        work_type  = request.GET.get('type', '').strip()
        query      = request.GET.get('q', '').strip()

        if work_type:
            works = works.filter(work_type=work_type)
        if query:
            works = works.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )

        context = {
            'works':        works,
            'work_types':   TeacherWork.WorkType.choices,
            'current_type': work_type,
            'current_query': query,
        }
        return render(request, self.template_name, context)


class TeacherWorkDetailView(View):
    """Bitta o'qituvchi ishi sahifasi."""
    template_name = 'main/work_detail.html'

    def get(self, request, pk):
        work = get_object_or_404(TeacherWork, pk=pk, is_published=True)
        TeacherWork.objects.filter(pk=pk).update(view_count=work.view_count + 1)
        return render(request, self.template_name, {'work': work})


# ─────────────────────────────────────────────────────────────────
#  AUTH VIEWS
# ─────────────────────────────────────────────────────────────────

class RegisterView(View):
    """
    Ro'yxatdan o'tish.
    Yangi user avtomatik 'student' roli bilan yaratiladi.
    """
    template_name = 'auth/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('main:home')
        return render(request, self.template_name, {'form': RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = User.Role.STUDENT   # har doim student bilan boshlanadi
            user.save()
            login(request, user)
            messages.success(request, "Xush kelibsiz! Ro'yxatdan o'tdingiz.")
            return redirect('main:home')
        return render(request, self.template_name, {'form': form})


class LoginView(View):
    """Tizimga kirish."""
    template_name = 'auth/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('main:home')
        return render(request, self.template_name, {'form': LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user     = authenticate(request, username=username, password=password)

            if user:
                login(request, user)
                next_url = request.GET.get('next', 'main:home')
                return redirect(next_url)
            else:
                messages.error(request, "Username yoki parol noto'g'ri.")

        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    """Tizimdan chiqish."""
    def post(self, request):
        logout(request)
        return redirect('main:home')


# ─────────────────────────────────────────────────────────────────
#  PROFIL VIEWS  (login bo'lgan har qanday user)
# ─────────────────────────────────────────────────────────────────

class ProfileView(LoginRequiredMixin, View):
    """
    Foydalanuvchi profili.
    Rol asosida turlicha ko'rinadi:
      - student  → saqlangan kitoblar
      - teacher  → o'z ishlari
      - admin    → dashboard ga yo'naltiriladi
    """
    template_name = 'main/profile.html'

    def get(self, request):
        user = request.user

        # Admin ni to'g'ridan-to'g'ri dashboard ga yo'naltirish
        if user.role == User.Role.ADMIN:
            return redirect('main:admin-dashboard')

        saved_books  = None
        works        = None
        has_pending  = False

        if user.role == User.Role.STUDENT:
            saved_books = SavedBook.objects.filter(user=user).select_related('book')
            has_pending = TeacherRequest.objects.filter(
                user=user, status=TeacherRequest.Status.PENDING
            ).exists()

        elif user.role == User.Role.TEACHER:
            works = TeacherWork.objects.filter(teacher=user).order_by('-created_at')

        unread_count = AdminMessage.objects.filter(recipient=user, is_read=False).count()

        context = {
            'profile_user': user,
            'saved_books':  saved_books,
            'works':        works,
            'has_pending':  has_pending,
            'unread_count': unread_count,
        }
        return render(request, self.template_name, context)


class ProfileEditView(LoginRequiredMixin, View):
    """Profilni tahrirlash (avatar, bio, phone)."""
    template_name = 'main/profile_edit.html'

    def get(self, request):
        form = ProfileEditForm(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil muvaffaqiyatli yangilandi.")
            return redirect('main:profile')
        return render(request, self.template_name, {'form': form})


class UserMessagesView(LoginRequiredMixin, View):
    """Foydalanuvchi qabul qilgan xabarlar ro'yxati."""
    template_name = 'main/user_messages.html'

    def get(self, request):
        msgs = AdminMessage.objects.filter(recipient=request.user).order_by('-created_at')
        return render(request, self.template_name, {'messages_list': msgs})


class MarkMessageReadView(LoginRequiredMixin, View):
    """Xabarni o'qilgan deb belgilash."""
    def post(self, request, pk):
        msg = get_object_or_404(AdminMessage, pk=pk, recipient=request.user)
        if not msg.is_read:
            msg.is_read = True
            msg.read_at = timezone.now()
            msg.save(update_fields=['is_read', 'read_at'])
        return redirect('main:user-messages')


# ─────────────────────────────────────────────────────────────────
#  TALABA VIEWS
# ─────────────────────────────────────────────────────────────────

class SaveBookView(LoginRequiredMixin, View):
    """Kitobni profilga saqlash."""
    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk, is_active=True)
        SavedBook.objects.get_or_create(user=request.user, book=book)
        messages.success(request, f"'{book.title}' kitob saqlandi.")
        return redirect('main:book-detail', pk=pk)


class UnsaveBookView(LoginRequiredMixin, View):
    """Saqlangan kitobni olib tashlash."""
    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        SavedBook.objects.filter(user=request.user, book=book).delete()
        messages.info(request, f"'{book.title}' kitob olib tashlandi.")
        return redirect('main:book-detail', pk=pk)


class SavedBooksView(LoginRequiredMixin, View):
    """Saqlangan kitoblar to'liq ro'yxati."""
    template_name = 'main/saved_books.html'

    def get(self, request):
        saved = SavedBook.objects.filter(user=request.user).select_related('book', 'book__category')
        return render(request, self.template_name, {'saved_books': saved})


class TeacherRequestView(LoginRequiredMixin, View):
    """
    O'qituvchilik maqomiga ariza topshirish.
    Faqat student role uchun. Pending ariza bo'lsa yangi ariza qabul qilinmaydi.
    """
    template_name = 'main/teacher_request.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role != User.Role.STUDENT:
            messages.warning(request, "Siz allaqachon o'qituvchi yoki admin maqomiga egasiz.")
            return redirect('main:profile')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        pending = TeacherRequest.objects.filter(
            user=request.user, status=TeacherRequest.Status.PENDING
        ).exists()
        form    = TeacherRequestForm()
        return render(request, self.template_name, {'form': form, 'pending': pending})

    def post(self, request):
        # Pending ariza borligini tekshirish
        if TeacherRequest.objects.filter(user=request.user, status=TeacherRequest.Status.PENDING).exists():
            messages.warning(request, "Sizning arizangiz hali ko'rib chiqilmoqda.")
            return redirect('main:profile')

        form = TeacherRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.user = request.user
            req.save()
            messages.success(request, "Ariza yuborildi. Admin ko'rib chiqadi.")
            return redirect('main:profile')

        return render(request, self.template_name, {'form': form, 'pending': False})


# ─────────────────────────────────────────────────────────────────
#  O'QITUVCHI VIEWS
# ─────────────────────────────────────────────────────────────────

class MyWorksView(TeacherRequiredMixin, View):
    """O'qituvchining o'z ishlari ro'yxati."""
    template_name = 'main/my_works.html'

    def get(self, request):
        works = TeacherWork.objects.filter(teacher=request.user).order_by('-created_at')
        return render(request, self.template_name, {'works': works})


class TeacherWorkCreateView(TeacherRequiredMixin, View):
    """Yangi qo'llanma / maqola yuklash."""
    template_name = 'main/work_form.html'

    def get(self, request):
        return render(request, self.template_name, {'form': TeacherWorkForm(), 'action': 'Qo\'shish'})

    def post(self, request):
        form = TeacherWorkForm(request.POST, request.FILES)
        if form.is_valid():
            work         = form.save(commit=False)
            work.teacher = request.user
            work.save()
            messages.success(request, "Ish muvaffaqiyatli yuklandi.")
            return redirect('main:my-works')
        return render(request, self.template_name, {'form': form, 'action': 'Qo\'shish'})


class TeacherWorkUpdateView(TeacherRequiredMixin, View):
    """Mavjud ishni tahrirlash. Faqat o'z ishi bo'lsa."""
    template_name = 'main/work_form.html'

    def get_work(self, request, pk):
        return get_object_or_404(TeacherWork, pk=pk, teacher=request.user)

    def get(self, request, pk):
        work = self.get_work(request, pk)
        form = TeacherWorkForm(instance=work)
        return render(request, self.template_name, {'form': form, 'action': 'Tahrirlash', 'work': work})

    def post(self, request, pk):
        work = self.get_work(request, pk)
        form = TeacherWorkForm(request.POST, request.FILES, instance=work)
        if form.is_valid():
            form.save()
            messages.success(request, "Ish yangilandi.")
            return redirect('main:my-works')
        return render(request, self.template_name, {'form': form, 'action': 'Tahrirlash', 'work': work})


class TeacherWorkDeleteView(TeacherRequiredMixin, View):
    """Ishni o'chirish. Faqat o'z ishi bo'lsa."""
    template_name = 'main/work_confirm_delete.html'

    def get_work(self, request, pk):
        return get_object_or_404(TeacherWork, pk=pk, teacher=request.user)

    def get(self, request, pk):
        work = self.get_work(request, pk)
        return render(request, self.template_name, {'work': work})

    def post(self, request, pk):
        work = self.get_work(request, pk)
        work.delete()
        messages.success(request, "Ish o'chirildi.")
        return redirect('main:my-works')


# ─────────────────────────────────────────────────────────────────
#  ADMIN PANEL VIEWS
# ─────────────────────────────────────────────────────────────────

class AdminDashboardView(AdminRequiredMixin, View):
    """
    Admin bosh sahifasi — umumiy statistika ko'rinishi.
    """
    template_name = 'admin_panel/dashboard.html'

    def get(self, request):
        context = {
            'total_users':    User.objects.count(),
            'total_students': User.objects.filter(role=User.Role.STUDENT).count(),
            'total_teachers': User.objects.filter(role=User.Role.TEACHER).count(),
            'total_books':    Book.objects.filter(is_active=True).count(),
            'total_works':    TeacherWork.objects.filter(is_published=True).count(),
            'pending_requests': TeacherRequest.objects.filter(
                status=TeacherRequest.Status.PENDING
            ).count(),
            'recent_users':   User.objects.order_by('-date_joined')[:5],
        }
        return render(request, self.template_name, context)


class AdminUserListView(AdminRequiredMixin, View):
    """Barcha foydalanuvchilar ro'yxati + qidiruv + rol filtr."""
    template_name = 'admin_panel/user_list.html'

    def get(self, request):
        users    = User.objects.all().order_by('-date_joined')
        query    = request.GET.get('q', '').strip()
        role     = request.GET.get('role', '').strip()

        if query:
            users = users.filter(
                Q(username__icontains=query) |
                Q(email__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )
        if role:
            users = users.filter(role=role)

        context = {
            'users':        users,
            'roles':        User.Role.choices,
            'current_role': role,
            'current_query': query,
        }
        return render(request, self.template_name, context)


class AdminUserDetailView(AdminRequiredMixin, View):
    """Foydalanuvchi profilini batafsil ko'rish."""
    template_name = 'admin_panel/user_detail.html'

    def get(self, request, pk):
        profile_user = get_object_or_404(User, pk=pk)
        requests     = TeacherRequest.objects.filter(user=profile_user).order_by('-created_at')
        sent_msgs    = AdminMessage.objects.filter(recipient=profile_user).order_by('-created_at')

        context = {
            'profile_user': profile_user,
            'requests':     requests,
            'sent_messages': sent_msgs,
        }
        return render(request, self.template_name, context)


class AdminUserToggleView(AdminRequiredMixin, View):
    """
    Foydalanuvchini faollashtirish / faolsizlantirish
    (is_active maydonini o'zgartirish).
    """
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)

        # Adminni o'chirib bo'lmaydi
        if user.role == User.Role.ADMIN:
            messages.error(request, "Admin foydalanuvchisini o'chirib bo'lmaydi.")
            return redirect('main:admin-user-detail', pk=pk)

        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        status = "faollashtirildi" if user.is_active else "faolsizlashtirildi"
        messages.success(request, f"{user.username} {status}.")
        return redirect('main:admin-user-detail', pk=pk)


class AdminTeacherRequestListView(AdminRequiredMixin, View):
    """O'qituvchilik arizalari ro'yxati. Status bo'yicha filtrlash."""
    template_name = 'admin_panel/teacher_request_list.html'

    def get(self, request):
        status   = request.GET.get('status', TeacherRequest.Status.PENDING)
        requests = TeacherRequest.objects.filter(status=status).select_related('user').order_by('-created_at')

        context = {
            'requests':       requests,
            'statuses':       TeacherRequest.Status.choices,
            'current_status': status,
        }
        return render(request, self.template_name, context)


class AdminTeacherRequestDetailView(AdminRequiredMixin, View):
    """Bitta ariza batafsil ko'rinishi."""
    template_name = 'admin_panel/teacher_request_detail.html'

    def get(self, request, pk):
        req = get_object_or_404(TeacherRequest, pk=pk)
        return render(request, self.template_name, {'req': req})


class AdminApproveRequestView(AdminRequiredMixin, View):
    """
    Arizani tasdiqlash:
      1. TeacherRequest.status → approved
      2. User.role → teacher
    """
    def post(self, request, pk):
        req = get_object_or_404(TeacherRequest, pk=pk, status=TeacherRequest.Status.PENDING)

        # Arizani yangilash
        req.status      = TeacherRequest.Status.APPROVED
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()
        req.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])

        # Foydalanuvchi rolini o'zgartirish
        req.user.role = User.Role.TEACHER
        req.user.save(update_fields=['role'])

        # Foydalanuvchiga xabar yuborish
        AdminMessage.objects.create(
            sender    = request.user,
            recipient = req.user,
            subject   = "O'qituvchilik arizangiz tasdiqlandi!",
            body      = (
                f"Hurmatli {req.user.get_full_name() or req.user.username},\n\n"
                "O'qituvchilik maqomiga arizangiz tasdiqlandi. "
                "Endi siz o'z qo'llanma va maqolalaringizni saytga yuklashingiz mumkin."
            ),
        )

        messages.success(request, f"{req.user.username} o'qituvchi maqomiga ko'tarildi.")
        return redirect('main:admin-teacher-requests')


class AdminRejectRequestView(AdminRequiredMixin, View):
    """
    Arizani rad etish:
      1. TeacherRequest.status → rejected
      2. Foydalanuvchi roliga tegmaydi (student bo'lib qoladi)
    """
    def post(self, request, pk):
        req = get_object_or_404(TeacherRequest, pk=pk, status=TeacherRequest.Status.PENDING)

        req.status      = TeacherRequest.Status.REJECTED
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()
        req.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])

        # Foydalanuvchiga xabar yuborish
        AdminMessage.objects.create(
            sender    = request.user,
            recipient = req.user,
            subject   = "O'qituvchilik arizangiz rad etildi",
            body      = (
                f"Hurmatli {req.user.get_full_name() or req.user.username},\n\n"
                "Afsuski, o'qituvchilik maqomiga arizangiz qabul qilinmadi. "
                "Qo'shimcha ma'lumot olish uchun biz bilan bog'laning."
            ),
        )

        messages.info(request, f"{req.user.username} arizasi rad etildi.")
        return redirect('main:admin-teacher-requests')


class AdminSendMessageView(AdminRequiredMixin, View):
    """Admin foydalanuvchiga xabar yuborish."""
    template_name = 'admin_panel/send_message.html'

    def get(self, request):
        form       = AdminMessageForm()
        recipients = User.objects.exclude(role=User.Role.ADMIN).order_by('username')
        return render(request, self.template_name, {'form': form, 'recipients': recipients})

    def post(self, request):
        form = AdminMessageForm(request.POST)
        if form.is_valid():
            msg        = form.save(commit=False)
            msg.sender = request.user
            msg.save()
            messages.success(request, f"Xabar '{msg.recipient.username}' ga yuborildi.")
            return redirect('main:admin-message-list')

        recipients = User.objects.exclude(role=User.Role.ADMIN).order_by('username')
        return render(request, self.template_name, {'form': form, 'recipients': recipients})


class AdminMessageListView(AdminRequiredMixin, View):
    """Admin yuborgan xabarlar tarixi."""
    template_name = 'admin_panel/message_list.html'

    def get(self, request):
        msgs = AdminMessage.objects.filter(sender=request.user).order_by('-created_at')
        return render(request, self.template_name, {'messages_list': msgs})


# ─── Kitoblar CRUD ───────────────────────────────────────────────

class AdminBookListView(AdminRequiredMixin, View):
    """Admin: barcha kitoblar ro'yxati."""
    template_name = 'admin_panel/book_list.html'

    def get(self, request):
        books = Book.objects.all().select_related('category', 'added_by').order_by('-created_at')
        query = request.GET.get('q', '').strip()
        if query:
            books = books.filter(
                Q(title__icontains=query) | Q(author__icontains=query)
            )
        return render(request, self.template_name, {'books': books, 'current_query': query})


class AdminBookCreateView(AdminRequiredMixin, View):
    """Yangi kitob qo'shish."""
    template_name = 'admin_panel/book_form.html'

    def get(self, request):
        return render(request, self.template_name, {'form': BookForm(), 'action': 'Qo\'shish'})

    def post(self, request):
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book          = form.save(commit=False)
            book.added_by = request.user
            book.save()
            messages.success(request, f"'{book.title}' kitob qo'shildi.")
            return redirect('main:admin-book-list')
        return render(request, self.template_name, {'form': form, 'action': 'Qo\'shish'})


class AdminBookUpdateView(AdminRequiredMixin, View):
    """Kitobni tahrirlash."""
    template_name = 'admin_panel/book_form.html'

    def get(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        return render(request, self.template_name, {'form': BookForm(instance=book), 'action': 'Tahrirlash', 'book': book})

    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{book.title}' yangilandi.")
            return redirect('main:admin-book-list')
        return render(request, self.template_name, {'form': form, 'action': 'Tahrirlash', 'book': book})


class AdminBookDeleteView(AdminRequiredMixin, View):
    """Kitobni o'chirish (is_active=False, to'liq o'chirish emas)."""
    template_name = 'admin_panel/book_confirm_delete.html'

    def get(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        return render(request, self.template_name, {'book': book})

    def post(self, request, pk):
        book          = get_object_or_404(Book, pk=pk)
        book.is_active = False
        book.save(update_fields=['is_active'])
        messages.success(request, f"'{book.title}' arxivlandi.")
        return redirect('main:admin-book-list')


# ─── Kategoriyalar CRUD ──────────────────────────────────────────

class AdminCategoryListView(AdminRequiredMixin, View):
    """Admin: kategoriyalar ro'yxati."""
    template_name = 'admin_panel/category_list.html'

    def get(self, request):
        categories = Category.objects.all().order_by('name')
        return render(request, self.template_name, {'categories': categories})


class AdminCategoryCreateView(AdminRequiredMixin, View):
    """Yangi kategoriya qo'shish."""
    template_name = 'admin_panel/category_form.html'

    def get(self, request):
        return render(request, self.template_name, {'form': CategoryForm(), 'action': 'Qo\'shish'})

    def post(self, request):
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f"'{cat.name}' kategoriyasi qo'shildi.")
            return redirect('main:admin-category-list')
        return render(request, self.template_name, {'form': form, 'action': 'Qo\'shish'})


class AdminCategoryUpdateView(AdminRequiredMixin, View):
    """Kategoriyani tahrirlash."""
    template_name = 'admin_panel/category_form.html'

    def get(self, request, pk):
        cat = get_object_or_404(Category, pk=pk)
        return render(request, self.template_name, {'form': CategoryForm(instance=cat), 'action': 'Tahrirlash', 'category': cat})

    def post(self, request, pk):
        cat  = get_object_or_404(Category, pk=pk)
        form = CategoryForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{cat.name}' yangilandi.")
            return redirect('main:admin-category-list')
        return render(request, self.template_name, {'form': form, 'action': 'Tahrirlash', 'category': cat})


class AdminCategoryDeleteView(AdminRequiredMixin, View):
    """Kategoriyani o'chirish."""
    template_name = 'admin_panel/category_confirm_delete.html'

    def get(self, request, pk):
        cat = get_object_or_404(Category, pk=pk)
        return render(request, self.template_name, {'category': cat})

    def post(self, request, pk):
        cat = get_object_or_404(Category, pk=pk)
        name = cat.name
        cat.delete()
        messages.success(request, f"'{name}' kategoriyasi o'chirildi.")
        return redirect('main:admin-category-list')
    
class ChatView(LoginRequiredMixin, View):
    template_name = 'main/chat.html'

    def get(self, request):
        return render(request, self.template_name)


class ChatAskView(LoginRequiredMixin, View):
    def post(self, request):
        from django.http import JsonResponse
        from .models import Book, TeacherWork

        try:
            data     = json.loads(request.body)
            prompt   = data.get('prompt', '').strip()
            history  = data.get('history', [])

            if not prompt:
                return JsonResponse({'error': 'Savol bo\'sh'}, status=400)

            # Mavjud kitoblar va o'qituvchi ishlarini yuborish
            book_names = list(Book.objects.filter(is_active=True).values_list('title', flat=True))
            work_names = list(TeacherWork.objects.filter(is_published=True).values_list('title', flat=True))
            all_names  = book_names + work_names

            answer = run_ai_prompt(
                prompt=prompt,
                user=request.user,
                book_name_list=all_names,
                history=history,
            )

            return JsonResponse({'answer': answer})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)