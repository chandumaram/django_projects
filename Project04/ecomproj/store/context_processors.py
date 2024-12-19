from .models import Category

def all_categories(request):
    categories = Category.objects.all()
    return {'all_categories':categories}

def search_query(request):
    query = request.GET.get('q', '')  # Get search query if available
    return {'search_query':query}