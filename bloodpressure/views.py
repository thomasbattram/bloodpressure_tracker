import matplotlib.pyplot as plt
from io import BytesIO
import base64
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import BloodPressure
from .forms import BloodPressureForm

def blood_pressure_list(request):
    blood_pressures = BloodPressure.objects.all().order_by('-measured_at')

    # Extract data for plotting
    systolic_values = [bp.systolic for bp in blood_pressures]
    diastolic_values = [bp.diastolic for bp in blood_pressures]
    measured_at_values = [bp.measured_at.strftime("%Y-%m-%d %H:%M:%S") for bp in blood_pressures]

    # Generate the plot
    plt.figure(figsize=(10, 6))
    plt.plot(measured_at_values, systolic_values, label='Systolic')
    plt.plot(measured_at_values, diastolic_values, label='Diastolic')
    plt.xlabel('Time')
    plt.ylabel('Blood Pressure')
    plt.title('Blood Pressure Over Time')
    plt.legend()

    # Convert the plot to an image for display
    image = BytesIO()
    plt.savefig(image, format='png')
    plt.close()
    image.seek(0)
    plot_url = base64.b64encode(image.getvalue()).decode()

    return render(request, 'bloodpressure/blood_pressure_list.html', {'blood_pressures': blood_pressures, 'plot_url': plot_url})

def add_blood_pressure(request):
    if request.method == 'POST':
        form = BloodPressureForm(request.POST)
        if form.is_valid():
            blood_pressure = form.save(commit=False)
            measured_at = form.cleaned_data['measured_at']
            blood_pressure.measured_at = measured_at.replace(tzinfo=None)
            blood_pressure.save()
            return redirect('blood_pressure_list')
    else:
        form = BloodPressureForm()
    return render(request, 'bloodpressure/add_blood_pressure.html', {'form': form})

def delete_blood_pressure(request, blood_pressure_id):
    blood_pressure = get_object_or_404(BloodPressure, id=blood_pressure_id)
    if request.method == 'POST':
        blood_pressure.delete()
        return redirect('blood_pressure_list')
    return render(request, 'bloodpressure/delete_blood_pressure.html', {'blood_pressure': blood_pressure})
