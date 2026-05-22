from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='Yessy').exists():
    User.objects.create_superuser('Yessy', 'yessy@papeleria.local', '1987')
    print("Usuario Yessy creado")
else:
    print("Usuario Yessy ya existe")
