from django.shortcuts import render

def termos_uso(request):
    return render(request, 'pages/termos.html')

def privacidade(request):
    return render(request, 'pages/privacidade.html')

def trocas_devolucoes(request):
    return render(request, 'pages/trocas.html')