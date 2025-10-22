from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from .models import Proveedor
from .forms import ProveedorForm, ProveedorContactoFormSet

@login_required
def proveedores_list(request):
    q = (request.GET.get("q") or "").strip()
    qs = Proveedor.objects.filter(owner=request.user)  # 👈 solo los del usuario

    if q:
        qs = qs.filter(
            Q(razon_social__icontains=q) |
            Q(rut__icontains=q) |
            Q(giro__icontains=q) |
            Q(email__icontains=q) |
            Q(telefono__icontains=q)
        )

    paginator = Paginator(qs.order_by("razon_social"), 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "proveedores/list.html", {"page_obj": page_obj, "q": q})

@login_required
def proveedores_create(request):
    if request.method == "POST":
        form = ProveedorForm(request.POST)
        if form.is_valid():
            proveedor = form.save(commit=False)
            proveedor.owner = request.user            # 👈 asigna dueño
            proveedor.save()
            # contactos opcionales
            formset = ProveedorContactoFormSet(request.POST, instance=proveedor)
            if formset.is_valid():
                formset.save()
            messages.success(request, "Proveedor creado correctamente.")
            return redirect("proveedores:proveedores_list")
        messages.error(request, "Revisa los campos marcados.")
        formset = ProveedorContactoFormSet(request.POST)
    else:
        form = ProveedorForm()
        formset = ProveedorContactoFormSet()
    return render(request, "proveedores/form.html", {"form": form, "formset": formset, "title": "Crear proveedor"})

@login_required
def proveedores_update(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk, owner=request.user)  # 👈 acceso restringido
    if request.method == "POST":
        form = ProveedorForm(request.POST, instance=proveedor)
        formset = ProveedorContactoFormSet(request.POST, instance=proveedor)
        if form.is_valid() and formset.is_valid():
            form.save()     # owner no cambia
            formset.save()
            messages.success(request, "Proveedor actualizado correctamente.")
            return redirect("proveedores:proveedores_list")
        messages.error(request, "Revisa los campos marcados.")
    else:
        form = ProveedorForm(instance=proveedor)
        formset = ProveedorContactoFormSet(instance=proveedor)
    return render(request, "proveedores/form.html", {"form": form, "formset": formset, "title": "Editar proveedor"})


@login_required
def proveedores_delete(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk, owner=request.user)
    if request.method == "POST":
        proveedor.delete()
        messages.success(request, "Proveedor eliminado correctamente.")
        return redirect("proveedores:proveedores_list")
    messages.error(request, "Acción no permitida.")
    return redirect("proveedor:proveedores_list")


@login_required
def proveedores_detail(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk, owner=request.user)  # 👈 acceso restringido
    return render(request, "proveedores/detail.html", {"proveedor": proveedor})


