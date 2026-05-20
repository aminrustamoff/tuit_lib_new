from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [

    # ─────────────────────────────────────────
    #  PUBLIC — Hamma ko'ra oladigan sahifalar
    # ─────────────────────────────────────────

    # Home page (statistika, kitoblar, registratsiya bo'limi)
    path('', views.HomeView.as_view(), name='home'),

    # Kitoblar ro'yxati (filter: kategoriya, qidiruv)
    path('books/', views.BookListView.as_view(), name='book-list'),

    # Bitta kitob sahifasi
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='book-detail'),

    # Kategoriya bo'yicha kitoblar
    path('category/<slug:slug>/', views.CategoryBooksView.as_view(), name='category-books'),

    # O'qituvchi ishlari ro'yxati (umumiy)
    path('works/', views.TeacherWorkListView.as_view(), name='work-list'),

    # Bitta o'qituvchi ishi sahifasi
    path('works/<int:pk>/', views.TeacherWorkDetailView.as_view(), name='work-detail'),


    # ─────────────────────────────────────────
    #  AUTH — Kirish / Ro'yxatdan o'tish
    # ─────────────────────────────────────────

    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/',    views.LoginView.as_view(),    name='login'),
    path('logout/',   views.LogoutView.as_view(),   name='logout'),


    # ─────────────────────────────────────────
    #  PROFIL — Login bo'lgan har qanday user
    # ─────────────────────────────────────────

    # Profilni ko'rish
    path('profile/', views.ProfileView.as_view(), name='profile'),

    # Profilni tahrirlash
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile-edit'),

    # Foydalanuvchining xabarlari (admin yuborgan)
    path('profile/messages/', views.UserMessagesView.as_view(), name='user-messages'),

    # Xabarni o'qilgan deb belgilash
    path('profile/messages/<int:pk>/read/', views.MarkMessageReadView.as_view(), name='message-read'),


    # ─────────────────────────────────────────
    #  TALABA — Kitob saqlash
    # ─────────────────────────────────────────

    # Kitobni profilga qo'shish / olib tashlash
    path('books/<int:pk>/save/',   views.SaveBookView.as_view(),   name='book-save'),
    path('books/<int:pk>/unsave/', views.UnsaveBookView.as_view(), name='book-unsave'),

    # Saqlangan kitoblar ro'yxati
    path('profile/saved-books/', views.SavedBooksView.as_view(), name='saved-books'),

    # O'qituvchilik maqomiga ariza topshirish
    path('profile/teacher-request/', views.TeacherRequestView.as_view(), name='teacher-request'),


    # ─────────────────────────────────────────
    #  O'QITUVCHI — "Mening ishlarim"
    # ─────────────────────────────────────────

    # O'z ishlari ro'yxati
    path('profile/my-works/', views.MyWorksView.as_view(), name='my-works'),

    # Yangi ish yuklash
    path('profile/my-works/add/', views.TeacherWorkCreateView.as_view(), name='work-create'),

    # Ishni tahrirlash
    path('profile/my-works/<int:pk>/edit/', views.TeacherWorkUpdateView.as_view(), name='work-edit'),

    # Ishni o'chirish
    path('profile/my-works/<int:pk>/delete/', views.TeacherWorkDeleteView.as_view(), name='work-delete'),


    # ─────────────────────────────────────────
    #  ADMIN PANEL — Faqat admin roli uchun
    # ─────────────────────────────────────────

    # Admin bosh sahifasi (umumiy ko'rinish)
    path('dashboard/', views.AdminDashboardView.as_view(), name='admin-dashboard'),

    # Foydalanuvchilar ro'yxati
    path('dashboard/users/', views.AdminUserListView.as_view(), name='admin-user-list'),

    # Foydalanuvchi profilini ko'rish
    path('dashboard/users/<int:pk>/', views.AdminUserDetailView.as_view(), name='admin-user-detail'),

    # Foydalanuvchini faolsizlantirish / faollashtirish
    path('dashboard/users/<int:pk>/toggle/', views.AdminUserToggleView.as_view(), name='admin-user-toggle'),

    # O'qituvchilik arizalari ro'yxati
    path('dashboard/teacher-requests/', views.AdminTeacherRequestListView.as_view(), name='admin-teacher-requests'),

    # Ariza ko'rish va qaror qabul qilish (approve / reject)
    path('dashboard/teacher-requests/<int:pk>/', views.AdminTeacherRequestDetailView.as_view(), name='admin-teacher-request-detail'),
    path('dashboard/teacher-requests/<int:pk>/approve/', views.AdminApproveRequestView.as_view(), name='admin-approve-request'),
    path('dashboard/teacher-requests/<int:pk>/reject/',  views.AdminRejectRequestView.as_view(),  name='admin-reject-request'),

    # Foydalanuvchiga xabar yuborish
    path('dashboard/messages/send/', views.AdminSendMessageView.as_view(), name='admin-send-message'),

    # Yuborilgan xabarlar tarixi
    path('dashboard/messages/', views.AdminMessageListView.as_view(), name='admin-message-list'),

    # Kitoblar boshqaruvi (CRUD)
    path('dashboard/books/',                   views.AdminBookListView.as_view(),   name='admin-book-list'),
    path('dashboard/books/add/',               views.AdminBookCreateView.as_view(), name='admin-book-create'),
    path('dashboard/books/<int:pk>/edit/',     views.AdminBookUpdateView.as_view(), name='admin-book-edit'),
    path('dashboard/books/<int:pk>/delete/',   views.AdminBookDeleteView.as_view(), name='admin-book-delete'),

    # Kategoriyalar boshqaruvi (CRUD)
    path('dashboard/categories/',              views.AdminCategoryListView.as_view(),   name='admin-category-list'),
    path('dashboard/categories/add/',          views.AdminCategoryCreateView.as_view(), name='admin-category-create'),
    path('dashboard/categories/<int:pk>/edit/',   views.AdminCategoryUpdateView.as_view(), name='admin-category-edit'),
    path('dashboard/categories/<int:pk>/delete/', views.AdminCategoryDeleteView.as_view(), name='admin-category-delete'),
    path('chat/', views.ChatView.as_view(), name='chat'),
    path('chat/ask/', views.ChatAskView.as_view(), name='chat-ask'),
]