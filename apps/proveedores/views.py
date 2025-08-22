from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ProveedorForm, ProveedorContactoFormSet
from .models import Proveedor

from .models import Proveedor
from .forms import ProveedorForm


@login_required
def proveedores_list(request):
    q = (request.GET.get("q") or "").strip()

    qs = Proveedor.objects.all()
    if q:
        qs = qs.filter(
            Q(razon_social__icontains=q) |
            Q(rut__icontains=q) |
            Q(giro__icontains=q) |
            Q(email__icontains=q) |
            Q(telefono__icontains=q)
        )

    qs = qs.order_by("razon_social")

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "proveedores/list.html", {
        "page_obj": page_obj,   # usa page_obj en el template
        "q": q,
    })


@login_required
def proveedores_create(request):
    if request.method == "POST":
        form = ProveedorForm(request.POST)
        if form.is_valid():
            proveedor = form.save()
            formset = ProveedorContactoFormSet(request.POST, instance=proveedor)
            if formset.is_valid():
                formset.save()
                messages.success(request, "Proveedor creado correctamente.")
                return redirect("proveedor:proveedores_list")
            else:
                # Si contacto viene malo, muestra ambos formularios
                messages.error(request, "Revisa los datos del contacto.")
        else:
            formset = ProveedorContactoFormSet(request.POST)  # sin instance aún
            messages.error(request, "Revisa los campos marcados.")
    else:
        form = ProveedorForm()
        formset = ProveedorContactoFormSet()

    return render(request, "proveedores/form.html", {
        "form": form,
        "formset": formset,
        "title": "Crear proveedor",
    })

@login_required
def proveedores_update(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)

    if request.method == "POST":
        form = ProveedorForm(request.POST, instance=proveedor)
        formset = ProveedorContactoFormSet(request.POST, instance=proveedor)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Proveedor actualizado correctamente.")
            return redirect("proveedor:proveedores_list")
        messages.error(request, "Revisa los campos marcados.")
    else:
        form = ProveedorForm(instance=proveedor)
        formset = ProveedorContactoFormSet(instance=proveedor)

    return render(request, "proveedores/form.html", {
        "form": form,
        "formset": formset,
        "title": "Editar proveedor",
    })


@login_required
def proveedores_detail(request, pk):
    """Detalle de un proveedor específico."""
    proveedor = get_object_or_404(Proveedor, pk=pk)
    return render(request, "proveedores/detail.html", {"proveedor": proveedor})
