import asyncio
import json
from datetime import date
from io import BytesIO
from unittest.mock import patch
from zipfile import ZipFile

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from PIL import Image

from apps.core.file_validation import (
    UploadValidationError,
    validate_csv_upload,
    validate_document_upload,
    validate_evidence_upload,
    validate_image_upload,
    validate_portfolio_upload,
)
from apps.core.infrastructure.models import (
    AnnouncementAcknowledgement,
    AuditLog,
    InstitutionalAnnouncement,
    InstitutionalEvent,
    InternalNotification,
)
from apps.core.interfaces.forms import InstitutionalAnnouncementForm, InstitutionalEventForm
from apps.core.realtime import user_notification_group
from apps.users.infrastructure.models import User


class UploadValidationTests(SimpleTestCase):
    @staticmethod
    def _png_file(name="evidencia.png"):
        content = BytesIO()
        Image.new("RGB", (2, 2), "white").save(content, format="PNG")
        return SimpleUploadedFile(name, content.getvalue(), content_type="image/png")

    @staticmethod
    def _webp_file(name="material.webp"):
        content = BytesIO()
        Image.new("RGB", (2, 2), "white").save(content, format="WEBP")
        return SimpleUploadedFile(name, content.getvalue(), content_type="image/webp")

    @staticmethod
    def _docx_file(name="informe.docx"):
        content = BytesIO()
        with ZipFile(content, "w") as archive:
            archive.writestr("[Content_Types].xml", "<Types />")
            archive.writestr("word/document.xml", "<document />")
        return SimpleUploadedFile(
            name,
            content.getvalue(),
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
        )

    def test_accepts_valid_pdf_and_restores_pointer(self):
        uploaded = SimpleUploadedFile(
            "norma.pdf", b"%PDF-1.7\ncontenido", content_type="application/pdf"
        )

        validate_document_upload(uploaded)

        self.assertEqual(uploaded.tell(), 0)
        self.assertEqual(uploaded.read(5), b"%PDF-")

    def test_rejects_html_disguised_as_pdf(self):
        uploaded = SimpleUploadedFile(
            "ataque.pdf", b"<html><script>alert(1)</script></html>", content_type="application/pdf"
        )

        with self.assertRaisesMessage(UploadValidationError, "PDF válido"):
            validate_document_upload(uploaded)

    def test_accepts_structurally_valid_docx(self):
        validate_document_upload(self._docx_file())

    def test_rejects_zip_disguised_as_docx(self):
        content = BytesIO()
        with ZipFile(content, "w") as archive:
            archive.writestr("archivo.txt", "sin documento Word")
        uploaded = SimpleUploadedFile(
            "informe.docx", content.getvalue(), content_type="application/zip"
        )

        with self.assertRaisesMessage(UploadValidationError, "Word válido"):
            validate_document_upload(uploaded)

    def test_accepts_valid_image_for_all_current_image_flows(self):
        validate_image_upload(self._png_file("material.png"))
        validate_evidence_upload(self._png_file("evidencia.png"))
        validate_portfolio_upload(self._png_file("ficha.png"))

    def test_accepts_valid_webp_for_material_images(self):
        validate_image_upload(self._webp_file())

    def test_rejects_fake_image(self):
        uploaded = SimpleUploadedFile(
            "material.png", b"esto no es una imagen", content_type="image/png"
        )

        with self.assertRaisesMessage(UploadValidationError, "imagen válida"):
            validate_image_upload(uploaded)

    def test_accepts_utf8_csv_and_restores_pointer(self):
        uploaded = SimpleUploadedFile(
            "matrícula.CSV",
            "dni;nombres\n12345678;José\n".encode("utf-8"),
            content_type="text/csv",
        )

        validate_csv_upload(uploaded)

        self.assertEqual(uploaded.tell(), 0)

    def test_rejects_binary_or_non_utf8_csv(self):
        binary = SimpleUploadedFile(
            "datos.csv", b"dni\x00nombre", content_type="text/csv"
        )
        non_utf8 = SimpleUploadedFile(
            "datos.csv", b"dni;nombres\n1;\xff", content_type="text/csv"
        )

        with self.assertRaisesMessage(UploadValidationError, "datos binarios"):
            validate_csv_upload(binary)
        with self.assertRaisesMessage(UploadValidationError, "UTF-8"):
            validate_csv_upload(non_utf8)

    def test_rejects_extension_and_declared_mime_mismatches(self):
        wrong_extension = SimpleUploadedFile(
            "script.exe", b"%PDF-1.7", content_type="application/pdf"
        )
        wrong_mime = SimpleUploadedFile(
            "norma.pdf", b"%PDF-1.7", content_type="text/html"
        )

        with self.assertRaisesMessage(UploadValidationError, "Formato no permitido"):
            validate_document_upload(wrong_extension)
        with self.assertRaisesMessage(UploadValidationError, "tipo declarado"):
            validate_document_upload(wrong_mime)

    def test_rejects_oversized_file_before_reading_its_content(self):
        uploaded = SimpleUploadedFile(
            "material.png", b"x" * (5 * 1024 * 1024 + 1), content_type="image/png"
        )

        with self.assertRaisesMessage(UploadValidationError, "5 MB"):
            validate_image_upload(uploaded)


class ComplementaryFeaturesTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            dni='70707070',
            password='ClaveDocente!2026',
            password_changed=True,
            role='DOCENTE',
            first_name='Rosa',
            last_name='Docente',
        )
        self.director = User.objects.create_user(
            dni='80808080',
            password='ClaveDirector!2026',
            password_changed=True,
            role='DIRECTOR',
            first_name='Carlos',
            last_name='Director',
        )
        self.parent = User.objects.create_user(
            dni='60606060',
            password='ClaveFamilia!2026',
            password_changed=True,
            role='APODERADO',
            first_name='Ana',
            last_name='Familia',
        )
        self.superuser = User.objects.create_superuser(
            dni='90909090',
            password='ClaveTecnica!2026',
            first_name='Soporte',
            last_name='Técnico',
        )
        self.other_notification = InternalNotification.objects.create(
            user=self.director,
            title='Aviso privado de dirección',
            message='Esta notificación no pertenece al docente.',
        )
        self.teacher_notification = InternalNotification.objects.create(
            user=self.teacher,
            title='Material disponible',
            message='Tu solicitud ya puede ser recogida.',
            link=reverse('warehouse:catalog'),
        )

    def test_notification_center_is_scoped_to_authenticated_user(self):
        self.client.force_login(self.teacher)

        response = self.client.get(reverse('core:notifications'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Material disponible')
        self.assertNotContains(response, 'Aviso privado de dirección')

    def test_notification_state_can_only_be_changed_by_its_owner(self):
        self.client.force_login(self.teacher)

        response = self.client.post(
            reverse('core:update_notification_state', args=[self.teacher_notification.id]),
            {'state': 'read'},
        )

        self.assertRedirects(response, reverse('core:notifications'))
        self.teacher_notification.refresh_from_db()
        self.assertTrue(self.teacher_notification.is_read)

        self.client.post(
            reverse('core:update_notification_state', args=[self.other_notification.id]),
            {'state': 'read'},
        )
        self.other_notification.refresh_from_db()
        self.assertFalse(self.other_notification.is_read)

    def test_external_notification_link_is_not_used_as_a_redirect(self):
        unsafe_notification = InternalNotification.objects.create(
            user=self.teacher,
            title='Enlace externo',
            message='Prueba de redirección segura.',
            link='https://example.invalid/phishing',
        )
        self.client.force_login(self.teacher)

        response = self.client.get(
            reverse('core:read_notification', args=[unsafe_notification.id])
        )

        self.assertRedirects(response, reverse('core:dashboard'))
        unsafe_notification.refresh_from_db()
        self.assertTrue(unsafe_notification.is_read)

    def test_orphan_announcement_notification_is_removed_safely(self):
        orphan = InternalNotification.objects.create(
            user=self.teacher,
            title='Comunicado retirado',
            message='Este comunicado ya no existe.',
            link='/comunicados/999999/',
        )
        self.client.force_login(self.teacher)

        response = self.client.get(
            reverse('core:read_notification', args=[orphan.pk])
        )

        self.assertRedirects(response, reverse('core:notifications'))
        self.assertFalse(InternalNotification.objects.filter(pk=orphan.pk).exists())

    def test_deleting_announcement_removes_its_linked_notifications(self):
        announcement = InstitutionalAnnouncement.objects.create(
            title='Comunicado temporal',
            message='Contenido temporal.',
            audience='TEACHERS',
            created_by=self.director,
        )
        detail_url = reverse('core:announcement_detail', args=[announcement.pk])
        linked = InternalNotification.objects.create(
            user=self.teacher,
            title='Comunicado temporal',
            message='Contenido temporal.',
            link=detail_url,
        )
        unrelated = InternalNotification.objects.create(
            user=self.teacher,
            title='Otra notificación',
            message='Debe conservarse.',
            link=reverse('core:calendar'),
        )

        announcement.delete()

        self.assertFalse(InternalNotification.objects.filter(pk=linked.pk).exists())
        self.assertTrue(InternalNotification.objects.filter(pk=unrelated.pk).exists())

    def test_audit_is_restricted_to_superusers(self):
        AuditLog.objects.create(
            user=self.teacher,
            action='UPDATE',
            model_name='Material',
            object_id='ACTIVIDAD-DOCENTE-UNICA',
            changes={'info': 'Registro del docente'},
        )
        AuditLog.objects.create(
            user=self.director,
            action='UPDATE',
            model_name='User',
            object_id='ACTIVIDAD-DIRECTOR-UNICA',
            changes={'info': 'Registro del director'},
        )

        self.client.force_login(self.director)
        director_response = self.client.get(reverse('core:activity'))
        self.assertEqual(director_response.status_code, 403)

        self.client.force_login(self.teacher)
        teacher_response = self.client.get(reverse('core:activity'))
        self.assertEqual(teacher_response.status_code, 403)

        self.client.force_login(self.superuser)
        technical_response = self.client.get(reverse('core:activity'))
        self.assertContains(technical_response, 'ACTIVIDAD-DOCENTE-UNICA')
        self.assertContains(technical_response, 'ACTIVIDAD-DIRECTOR-UNICA')

    def test_login_does_not_create_a_redundant_user_update(self):
        user_logs = AuditLog.objects.filter(
            model_name='User',
            object_id=str(self.teacher.pk),
        )
        user_logs.delete()

        self.client.force_login(self.teacher)

        self.assertEqual(user_logs.filter(action='LOGIN').count(), 1)
        self.assertFalse(user_logs.filter(action='UPDATE').exists())

    def test_event_form_uses_day_month_year_format(self):
        valid_form = InstitutionalEventForm(data={
            'title': 'Aniversario local',
            'description': 'Asueto institucional.',
            'event_kind': 'HOLIDAY',
            'event_date': '28/07/2027',
        })
        invalid_form = InstitutionalEventForm(data={
            'title': 'Fecha inválida',
            'description': 'No debe usar el formato estadounidense.',
            'event_kind': 'ACTIVITY',
            'event_date': '12/31/2027',
        })

        self.assertTrue(valid_form.is_valid(), valid_form.errors)
        self.assertEqual(valid_form.cleaned_data['event_date'], date(2027, 7, 28))
        self.assertFalse(invalid_form.is_valid())

    def test_announcement_optional_event_date_uses_day_month_year_format(self):
        valid_form = InstitutionalAnnouncementForm(data={
            'title': 'Inicio del campeonato escolar',
            'message': 'Actividad deportiva de la institución.',
            'audience': 'ALL',
            'event_date': '18/09/2027',
            'valid_until': '18/09/2027',
        })
        invalid_form = InstitutionalAnnouncementForm(data={
            'title': 'Fecha inválida',
            'message': 'Formato inválido.',
            'audience': 'ALL',
            'event_date': '09/18/2027',
        })

        self.assertTrue(valid_form.is_valid(), valid_form.errors)
        self.assertEqual(valid_form.cleaned_data['event_date'], date(2027, 9, 18))
        self.assertFalse(invalid_form.is_valid())

    def test_only_director_can_create_calendar_dates(self):
        payload = {
            'title': 'Asueto por aniversario',
            'description': 'Suspensión de actividades por aniversario institucional.',
            'event_kind': 'HOLIDAY',
            'event_date': '28/07/2027',
        }
        self.client.force_login(self.teacher)
        forbidden = self.client.post(reverse('core:create_event'), payload)
        self.assertEqual(forbidden.status_code, 403)

        self.client.force_login(self.director)
        response = self.client.post(reverse('core:create_event'), payload)

        self.assertRedirects(response, reverse('core:calendar'))
        event = InstitutionalEvent.objects.get(title='Asueto por aniversario')
        self.assertEqual(event.event_date, date(2027, 7, 28))
        self.assertTrue(event.is_holiday)
        self.assertTrue(InternalNotification.objects.filter(
            user=self.teacher,
            title='Nueva fecha institucional',
        ).exists())
        self.assertTrue(InternalNotification.objects.filter(
            user=self.parent,
            title='Nueva fecha institucional',
        ).exists())

    def test_director_can_edit_and_delete_calendar_date(self):
        event = InstitutionalEvent.objects.create(
            title='Reunión original',
            description='Descripción original.',
            event_date=date(2027, 8, 10),
        )
        event_link = f'/calendario/?event={event.pk}'
        notification = InternalNotification.objects.create(
            user=self.teacher,
            title='Nueva fecha institucional',
            message='Reunión original — 10/08/2027.',
            link=event_link,
        )
        self.client.force_login(self.teacher)
        self.assertEqual(
            self.client.post(reverse('core:edit_event', args=[event.pk]), {}).status_code,
            403,
        )

        self.client.force_login(self.director)
        edit_form = self.client.get(reverse('core:edit_event', args=[event.pk]))
        self.assertContains(edit_form, 'value="10/08/2027"')
        edited = self.client.post(reverse('core:edit_event', args=[event.pk]), {
            'title': 'Reunión actualizada',
            'description': 'Descripción actualizada.',
            'event_kind': 'ACTIVITY',
            'event_date': '12/08/2027',
        })
        self.assertRedirects(edited, reverse('core:calendar'))
        event.refresh_from_db()
        notification.refresh_from_db()
        self.assertEqual(event.title, 'Reunión actualizada')
        self.assertIn('12/08/2027', notification.message)

        confirmation = self.client.get(reverse('core:delete_event', args=[event.pk]))
        self.assertContains(confirmation, 'Eliminar fecha institucional')
        deleted = self.client.post(reverse('core:delete_event', args=[event.pk]))
        self.assertRedirects(deleted, reverse('core:calendar'))
        self.assertFalse(InstitutionalEvent.objects.filter(pk=event.pk).exists())
        self.assertFalse(InternalNotification.objects.filter(pk=notification.pk).exists())

    def test_calendar_api_exposes_human_date_as_day_month_year(self):
        InstitutionalEvent.objects.create(
            title='Actividad de prueba',
            description='Descripción.',
            event_date=date(2027, 9, 18),
        )
        self.client.force_login(self.teacher)

        response = self.client.get(reverse('core:api_calendar'), {
            'start': '2027-09-01T00:00:00Z',
            'end': '2027-10-01T00:00:00Z',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['extendedProps']['display_date'], '18/09/2027')

    def test_announcement_is_private_targeted_and_acknowledged(self):
        self.client.force_login(self.director)
        response = self.client.post(reverse('core:create_announcement'), {
            'title': 'Reunión pedagógica',
            'message': 'La reunión docente será el viernes a las 15:00.',
            'audience': 'TEACHERS',
            'event_date': '15/10/2027',
            'valid_until': '31/12/2027',
        })

        announcement = InstitutionalAnnouncement.objects.get(title='Reunión pedagógica')
        self.assertRedirects(
            response,
            reverse('core:announcement_detail', args=[announcement.pk]),
        )
        notification = InternalNotification.objects.get(
            user=self.teacher,
            link=reverse('core:announcement_detail', args=[announcement.pk]),
        )
        self.assertFalse(InternalNotification.objects.filter(
            user=self.parent,
            link=reverse('core:announcement_detail', args=[announcement.pk]),
        ).exists())

        self.client.force_login(self.teacher)
        teacher_calendar = self.client.get(reverse('core:api_calendar'), {
            'start': '2027-10-01T00:00:00Z',
            'end': '2027-11-01T00:00:00Z',
        })
        announcement_event = next(
            item for item in teacher_calendar.json()
            if item['id'] == f'announcement-{announcement.pk}'
        )
        self.assertEqual(announcement_event['backgroundColor'], '#7C3AED')
        self.assertTrue(announcement_event['extendedProps']['is_announcement'])

        self.client.force_login(self.parent)
        self.assertEqual(
            self.client.get(reverse('core:announcement_detail', args=[announcement.pk])).status_code,
            403,
        )

        self.client.force_login(self.teacher)
        first_page = self.client.get(reverse('core:calendar'))
        self.assertEqual(first_page.context['pending_announcement'], announcement)
        self.assertContains(first_page, 'Al confirmar, quedará registrada')

        acknowledgement = self.client.post(
            reverse('core:acknowledge_announcement', args=[announcement.pk]),
            {'next': reverse('core:calendar')},
        )
        self.assertRedirects(acknowledgement, reverse('core:calendar'))
        self.assertTrue(AnnouncementAcknowledgement.objects.filter(
            announcement=announcement,
            user=self.teacher,
        ).exists())
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        after_acknowledgement = self.client.get(reverse('core:calendar'))
        self.assertIsNone(after_acknowledgement.context.get('pending_announcement'))

        self.client.force_login(self.director)
        director_calendar = self.client.get(reverse('core:calendar'))
        listed_announcement = director_calendar.context['recent_announcements'][0]
        self.assertEqual(listed_announcement.acknowledgement_count, 1)
        reader_report = self.client.get(
            reverse('core:announcement_detail', args=[announcement.pk])
        )
        self.assertContains(reader_report, 'Constancias de lectura')
        self.assertContains(reader_report, self.teacher.dni)
        self.assertContains(reader_report, 'Confirmada')

        self.client.force_login(self.teacher)
        forbidden_toggle = self.client.post(
            reverse('core:toggle_announcement', args=[announcement.pk])
        )
        self.assertEqual(forbidden_toggle.status_code, 403)

        self.client.force_login(self.director)
        toggle_response = self.client.post(
            reverse('core:toggle_announcement', args=[announcement.pk])
        )
        self.assertRedirects(
            toggle_response,
            reverse('core:announcement_detail', args=[announcement.pk]),
        )
        announcement.refresh_from_db()
        self.assertFalse(announcement.is_active)

    def test_acknowledgement_is_emitted_live_to_director_report(self):
        announcement = InstitutionalAnnouncement.objects.create(
            title='Feria de ciencias',
            message='Presentación de proyectos.',
            audience='TEACHERS',
            created_by=self.director,
        )
        detail_url = reverse('core:announcement_detail', args=[announcement.pk])
        InternalNotification.objects.create(
            user=self.teacher,
            title=announcement.title,
            message=announcement.message,
            link=detail_url,
        )
        layer = get_channel_layer()
        channel_name = async_to_sync(layer.new_channel)()
        group_name = 'announcement_read_receipts'
        async_to_sync(layer.group_add)(group_name, channel_name)

        async def receive_event():
            return await asyncio.wait_for(layer.receive(channel_name), timeout=1)

        try:
            self.client.force_login(self.teacher)
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(
                    reverse('core:acknowledge_announcement', args=[announcement.pk])
                )
            event = async_to_sync(receive_event)()
        finally:
            async_to_sync(layer.group_discard)(group_name, channel_name)

        self.assertRedirects(response, detail_url)
        self.assertEqual(event['alert_type'], 'announcement_acknowledged')
        self.assertEqual(event['announcement_id'], announcement.pk)
        self.assertEqual(event['user_id'], self.teacher.pk)
        self.assertEqual(event['confirmed_count'], 1)
        self.assertEqual(event['pending_count'], 0)

    def test_editing_announcement_resynchronizes_its_audience(self):
        announcement = InstitutionalAnnouncement.objects.create(
            title='Aviso docente',
            message='Contenido inicial.',
            audience='TEACHERS',
            event_date=date(2027, 10, 19),
            created_by=self.director,
        )
        detail_url = reverse('core:announcement_detail', args=[announcement.pk])
        teacher_notification = InternalNotification.objects.create(
            user=self.teacher,
            title='Nuevo comunicado: Aviso docente',
            message='Contenido inicial.',
            link=detail_url,
        )
        self.client.force_login(self.teacher)
        self.assertEqual(
            self.client.get(reverse('core:edit_announcement', args=[announcement.pk])).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(reverse('core:delete_announcement', args=[announcement.pk])).status_code,
            403,
        )

        self.client.force_login(self.director)

        edit_form = self.client.get(
            reverse('core:edit_announcement', args=[announcement.pk])
        )
        self.assertContains(edit_form, 'value="19/10/2027"')

        response = self.client.post(
            reverse('core:edit_announcement', args=[announcement.pk]),
            {
                'title': 'Aviso para familias',
                'message': 'Contenido actualizado.',
                'audience': 'PARENTS',
                'event_date': '20/10/2027',
                'valid_until': '20/10/2027',
            },
        )

        self.assertRedirects(response, detail_url)
        announcement.refresh_from_db()
        self.assertEqual(announcement.title, 'Aviso para familias')
        self.assertFalse(InternalNotification.objects.filter(pk=teacher_notification.pk).exists())
        self.assertTrue(InternalNotification.objects.filter(
            user=self.parent,
            link=detail_url,
            title='Nuevo comunicado: Aviso para familias',
        ).exists())

        confirmation = self.client.get(
            reverse('core:delete_announcement', args=[announcement.pk])
        )
        self.assertContains(confirmation, 'Eliminar comunicado')
        self.client.post(reverse('core:delete_announcement', args=[announcement.pk]))
        self.assertFalse(InstitutionalAnnouncement.objects.filter(pk=announcement.pk).exists())
        self.assertFalse(InternalNotification.objects.filter(link=detail_url).exists())

    def test_public_landing_never_exposes_internal_announcements(self):
        announcement = InstitutionalAnnouncement.objects.create(
            title='INTERNAL-ANNOUNCEMENT-NOT-PUBLIC',
            message='Contenido reservado para las cuentas institucionales.',
            audience='ALL',
            created_by=self.director,
        )

        public_response = self.client.get(reverse('core:home'))
        self.assertNotContains(public_response, announcement.title)
        self.assertContains(public_response, 'Información institucional protegida')
        self.assertNotContains(public_response, 'Noticias y Anuncios')

        self.client.force_login(self.parent)
        parent_response = self.client.get(reverse('academics:parent_dashboard'))
        self.assertContains(parent_response, announcement.title)
        self.assertEqual(parent_response.context['pending_announcement'], announcement)

    @patch('apps.core.management.commands.load_holidays.urllib.request.urlopen')
    def test_holiday_command_is_idempotent(self, mocked_urlopen):
        payload = json.dumps([{
            'date': '2027-07-28',
            'localName': 'Fiestas Patrias',
            'global': True,
        }]).encode('utf-8')
        mocked_urlopen.return_value.__enter__.return_value.read.return_value = payload

        call_command('load_holidays', year=2027, strict=True)
        call_command('load_holidays', year=2027, strict=True)

        self.assertEqual(InstitutionalEvent.objects.filter(
            event_date=date(2027, 7, 28),
            is_holiday=True,
        ).count(), 1)

    def test_persisted_notification_is_emitted_to_private_websocket_group(self):
        layer = get_channel_layer()
        channel_name = async_to_sync(layer.new_channel)()
        group_name = user_notification_group(self.teacher.pk)
        async_to_sync(layer.group_add)(group_name, channel_name)

        async def receive_event():
            return await asyncio.wait_for(layer.receive(channel_name), timeout=1)

        try:
            with self.captureOnCommitCallbacks(execute=True):
                notification = InternalNotification.objects.create(
                    user=self.teacher,
                    title='Aviso WebSocket',
                    message='Mensaje entregado al canal privado.',
                    link='/notificaciones/',
                )
            event = async_to_sync(receive_event)()
        finally:
            async_to_sync(layer.group_discard)(group_name, channel_name)

        self.assertEqual(event['alert_type'], 'notification')
        self.assertEqual(event['notification_id'], notification.pk)
        self.assertEqual(event['title'], 'Aviso WebSocket')
