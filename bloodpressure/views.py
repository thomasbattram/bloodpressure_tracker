import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, DayLocator
from io import BytesIO
import base64, io, threading
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
import pandas as pd
from django.http import HttpResponse
from django.core.mail import EmailMessage
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Image, Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from PIL import Image as PilImage
from .models import BloodPressure
from .forms import BloodPressureForm

def blood_pressure_list(request):
    blood_pressures = BloodPressure.objects.all().order_by('measured_at')

    # Extract data for plotting
    systolic_values = [bp.systolic for bp in blood_pressures]
    diastolic_values = [bp.diastolic for bp in blood_pressures]
    measured_at_values = [bp.measured_at for bp in blood_pressures]

    # Generate the plot with lines and markers
    plt.figure(figsize=(10, 6))
    plt.plot(measured_at_values, systolic_values, marker='o', label='Systolic', linestyle='-', color='blue')
    plt.plot(measured_at_values, diastolic_values, marker='o', label='Diastolic', linestyle='-', color='green')
    
    # Draw red dashed lines at y=140 and y=90
    plt.axhline(y=140, color='red', linestyle='--')
    plt.axhline(y=90, color='red', linestyle='--')
    
    # Format X-axis as dates for the data points only
    date_format = DateFormatter("%Y-%m-%d")
    plt.gca().xaxis.set_major_formatter(date_format)
    plt.gca().xaxis.set_tick_params() 
    
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

def download_data_excel(request):
    blood_pressures = BloodPressure.objects.all().order_by('measured_at')
    df = pd.DataFrame(list(blood_pressures.values('systolic', 'diastolic', 'measured_at')))
    df['measured_at'] = df['measured_at'].dt.strftime('%Y-%m-%d %H:%M:%S')

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=blood_pressure_data.xlsx'

    df.to_excel(response, index=False)
    return response

def generate_pdf_and_send_email(request):
    # Blood pressure data
    blood_pressures = BloodPressure.objects.all().order_by('measured_at')
    systolic_values = [bp.systolic for bp in blood_pressures]
    diastolic_values = [bp.diastolic for bp in blood_pressures]
    measured_at_values = [bp.measured_at for bp in blood_pressures]

    # Create a PDF containing the graph and data
    buffer = io.BytesIO()

    # Generate the plot with lines and markers
    plt.figure(figsize=(10, 6))
    plt.plot(measured_at_values, systolic_values, marker='o', label='Systolic', linestyle='-', color='blue')
    plt.plot(measured_at_values, diastolic_values, marker='o', label='Diastolic', linestyle='-', color='green')
    plt.axhline(y=140, color='red', linestyle='--')
    plt.axhline(y=90, color='red', linestyle='--')
    plt.xlabel('Time')
    plt.ylabel('Blood Pressure')
    plt.title('Blood Pressure Over Time')
    plt.legend()

    # Format X-axis as dates with only the date (no time)
    date_format = DateFormatter("%Y-%m-%d")
    plt.gca().xaxis.set_major_formatter(date_format)
    plt.gca().xaxis.set_major_locator(DayLocator(interval=14))  # Show major ticks for every two weeks

    # Save the plot as an image file (PNG)
    plot_buffer = io.BytesIO()
    plt.savefig(plot_buffer, format='png', dpi=800)
    plt.close()
    plot_buffer.seek(0)

    # Create a PDF document
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    story = []

    # Add the plot image to the story
    img = PilImage.open(plot_buffer)
    img_width = 500  # Adjust the width of the image
    aspect_ratio = img.width / img.height
    img_height = img_width / aspect_ratio

    story.append(Paragraph('<b>Blood Pressure Over Time</b>', getSampleStyleSheet()['Heading1']))
    story.append(Paragraph('<br/><br/>', getSampleStyleSheet()['BodyText']))
    story.append(Paragraph('<b>Graph:</b>', getSampleStyleSheet()['Heading2']))
    story.append(Paragraph('<br/>', getSampleStyleSheet()['BodyText']))

    with io.BytesIO() as plot_buffer_pil:
        img = img.resize((int(img_width), int(img_height)), PilImage.ANTIALIAS)
        img.save(plot_buffer_pil, format='png')
        plot_data = plot_buffer_pil.getvalue()

    story.append(Image(io.BytesIO(plot_data), width=img_width, height=img_height))
    story.append(PageBreak())  # Add a page break

    # Add the table for the data
    table_data = [['Systolic', 'Diastolic', 'Measured At']]
    for bp in blood_pressures:
        table_data.append([bp.systolic, bp.diastolic, bp.measured_at.strftime('%Y-%m-%d %H:%M:%S')])

    table = Table(table_data)
    table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                               ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                               ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                               ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                               ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                               ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                               ('GRID', (0, 0), (-1, -1), 1, colors.black)]))

    story.append(Paragraph('<b>Table Data:</b>', getSampleStyleSheet()['Heading2']))
    story.append(Paragraph('<br/>', getSampleStyleSheet()['BodyText']))
    story.append(table)

    # Build the PDF document
    doc.build(story)

    # Send the PDF by email
    subject = 'Blood Pressure Data PDF'
    message = 'Please find your blood pressure data PDF attached.'
    from_email = 'thomas.battram@hotmail.co.uk'
    to_email = 'thomas.battram@hotmail.co.uk'

    email = EmailMessage(subject, message, from_email, [to_email])
    email.attach('blood_pressure_data.pdf', buffer.getvalue(), 'application/pdf')
    email.send()

    buffer.close()
    return HttpResponse('Email sent with PDF attachment.')

def download_pdf(request):
    # Blood pressure data
    blood_pressures = BloodPressure.objects.all().order_by('measured_at')
    systolic_values = [bp.systolic for bp in blood_pressures]
    diastolic_values = [bp.diastolic for bp in blood_pressures]
    measured_at_values = [bp.measured_at for bp in blood_pressures]

    # Create a PDF containing the graph and data
    buffer = io.BytesIO()

    # Generate the plot with lines and markers
    plt.figure(figsize=(10, 6))
    plt.plot(measured_at_values, systolic_values, marker='o', label='Systolic', linestyle='-', color='blue')
    plt.plot(measured_at_values, diastolic_values, marker='o', label='Diastolic', linestyle='-', color='green')
    plt.axhline(y=140, color='red', linestyle='--')
    plt.axhline(y=90, color='red', linestyle='--')
    plt.xlabel('Time')
    plt.ylabel('Blood Pressure')
    plt.title('Blood Pressure Over Time')
    plt.legend()

    # Format X-axis as dates with only the date (no time)
    date_format = DateFormatter("%Y-%m-%d")
    plt.gca().xaxis.set_major_formatter(date_format)
    plt.gca().xaxis.set_major_locator(DayLocator(interval=14))  # Show major ticks for every two weeks

    # Save the plot as an image file (PNG)
    plot_buffer = io.BytesIO()
    plt.savefig(plot_buffer, format='png', dpi=800)
    plt.close()
    plot_buffer.seek(0)

    # Create a PDF document
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    story = []

    # Add the plot image to the story
    img = PilImage.open(plot_buffer)
    img_width = 500  # Adjust the width of the image
    aspect_ratio = img.width / img.height
    img_height = img_width / aspect_ratio

    story.append(Paragraph('<b>Blood Pressure Over Time</b>', getSampleStyleSheet()['Heading1']))
    story.append(Paragraph('<br/><br/>', getSampleStyleSheet()['BodyText']))
    story.append(Paragraph('<b>Graph:</b>', getSampleStyleSheet()['Heading2']))
    story.append(Paragraph('<br/>', getSampleStyleSheet()['BodyText']))

    with io.BytesIO() as plot_buffer_pil:
        img = img.resize((int(img_width), int(img_height)), PilImage.ANTIALIAS)
        img.save(plot_buffer_pil, format='png')
        plot_data = plot_buffer_pil.getvalue()

    story.append(Image(io.BytesIO(plot_data), width=img_width, height=img_height))
    story.append(PageBreak())  # Add a page break

    # Add the table for the data
    table_data = [['Systolic', 'Diastolic', 'Measured At']]
    for bp in blood_pressures:
        table_data.append([bp.systolic, bp.diastolic, bp.measured_at.strftime('%Y-%m-%d %H:%M:%S')])

    table = Table(table_data)
    table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                               ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                               ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                               ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                               ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                               ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                               ('GRID', (0, 0), (-1, -1), 1, colors.black)]))

    story.append(Paragraph('<b>Table Data:</b>', getSampleStyleSheet()['Heading2']))
    story.append(Paragraph('<br/>', getSampleStyleSheet()['BodyText']))
    story.append(table)

    # Build the PDF document
    doc.build(story)

    # Return the PDF as a response for download
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="blood_pressure_data.pdf"'
    buffer.close()
    return response


# def download_pdf(request):
#     # Blood pressure data
#     blood_pressures = BloodPressure.objects.all().order_by('measured_at')
#     systolic_values = [bp.systolic for bp in blood_pressures]
#     diastolic_values = [bp.diastolic for bp in blood_pressures]
#     measured_at_values = [bp.measured_at.strftime('%Y-%m-%d %H:%M:%S') for bp in blood_pressures]

#     # Create a PDF containing the graph and data
#     buffer = io.BytesIO()

#     # ... (Same PDF generation code as in the generate_pdf_and_send_email view)

#     # Return the PDF as a response for download
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = 'attachment; filename="blood_pressure_data.pdf"'
#     response.write(buffer.getvalue())
#     buffer.close()
#     return response
