from django.http import JsonResponse


def health(request):
    """Simple endpoint to ensure the bot app is wired up."""
    return JsonResponse({"status": "ok"})

