from django.shortcuts import render, HttpResponse, redirect
from facturasAI.chatBox import main
import json
# Create your views here.


def home(request):
    return render(request, "manejo_facturas/home.html")


def facturas_view(request):
    if request.method == 'POST':
        if 'clear_table' in request.POST:  # Si se preciono el de limpiar tabla se borra toda la tabla y se recarga la pagina
            request.session['table_data'] = []
            return redirect('facturas')
        else:
            results = main()  # Se corre el main

            # Se agarra la lista que ya existe este vacia o no
            existing_table_data = request.session.get('table_data', [])

            if results:  # Si minimo puso un archivo
                # se hace una lista de diccionarios
                new_table_data = []
                for file_path, status in results.items():
                    new_table_data.append(
                        {'file_path': file_path, 'status': status})

                # junto ambas tabals
                updated_table_data = existing_table_data + new_table_data

                # Guardar la lista actualizada en la sesión
                request.session['table_data'] = updated_table_data

                # recarga la página de facturas para mostrar la tabla actualizada
                return redirect('facturas')
            else:
                # Si no hay ningun archivo manda un mensaje de error si hay archivos solo se vuelve a mostrar la tabala que ya estaga
                return render(request, "manejo_facturas/facturas.html", {'table_data': existing_table_data})

    else:  # Si vuelve a entrar se carga la tabla que estaba anteriormente. Claro si no fue borrada
        table_data = request.session.get('table_data', [])
        return render(request, "manejo_facturas/facturas.html", {'table_data': table_data})


def pedimentos_view(request):
    return render(request, "manejo_facturas/pedimentos.html")


def transferencias_view(request):
    return render(request, "manejo_facturas/transferencias.html")
