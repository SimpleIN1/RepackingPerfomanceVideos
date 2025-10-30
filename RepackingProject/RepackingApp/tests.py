import datetime
import subprocess
import time
import uuid
from typing import List

from lxml import etree
from django.db.models import Q
from django.forms.models import model_to_dict
from django.core.exceptions import ValidationError
from django.test import TestCase, Client, RequestFactory

from RepackingApp.forms import ProcessRecordingsForm
from RepackingApp.models import RecordingModel, TypeRecordingModel, RecordingTaskIdModel
from RepackingApp.services.records import request_recordings, parse_xml_recordings, \
    parse_xml_type_recording, parse_xml_recording, is_xml_element_or_not_none, upload_recordings_to_db, \
    get_type_recordings, \
    upload_from_source, get_recordings_foreinkey_type_recording, get_recordings_to_dict, get_type_recordings_to_dict, \
    update_recordings_fields, \
    upload_recordings_and_update_fields, get_recording, update_recording_by_record_id, update_recordings
from RepackingApp.services.record_task import create_recording_task, delete_recordings_tasks, get_recording_tasks, \
    update_recording_tasks, create_recording_tasks
from RepackingApp.validators import validate_recording_id


class RepackingServiceTests(TestCase):
    def setUp(self):
        self.content = \
            """
            <response>
              <returncode>SUCCESS</returncode>
              <recordings><recording><recordID>37c8d0e83c429289a34173f15ecc33fe05b2aa96-1676974666046</recordID><meetingID>ewfsozr1hyeu4y9iru6hdw05qtcifv1tqhnjn2v8</meetingID><internalMeetingID>37c8d0e83c429289a34173f15ecc33fe05b2aa96-1676974666046</internalMeetingID><name>Информационные технологии в задачах филологии и компьютерной лингвистики</name><isBreakout>false</isBreakout><published>true</published><state>published</state><startTime>1676974666046</startTime><endTime>1676978771753</endTime><participants>15</participants><rawSize>345908205</rawSize><metadata><bbb-origin-version>v2-a8e12df</bbb-origin-version><meetingName>Информационные технологии в задачах филологии и компьютерной лингвистики</meetingName><meetingId>ewfsozr1hyeu4y9iru6hdw05qtcifv1tqhnjn2v8</meetingId><gl-listed>false</gl-listed><bbb-origin>Greenlight</bbb-origin><isBreakout>false</isBreakout><bbb-origin-server-name>vcs-6.ict.nsc.ru</bbb-origin-server-name></metadata><size>175740599</size><playback><format><type>presentation</type><url>https://vcs-6.ict.nsc.ru/playback/presentation/2.3/37c8d0e83c429289a34173f15ecc33fe05b2aa96-1676974666046</url><processingTime>996111</processingTime><length>50</length><size>175740599</size></format></playback><data/></recording><recording><recordID>4d7c4b3f965fc189d9c6cb8ab68b0b07550bfb03-1633423215293</recordID><meetingID>r3za1pj6yh6fliywgdozrwfqesdfq7g5vjn00sbu</meetingID><internalMeetingID>4d7c4b3f965fc189d9c6cb8ab68b0b07550bfb03-1633423215293</internalMeetingID><name>Семинар ИВТ 16-00</name><isBreakout>false</isBreakout><published>true</published><state>published</state><startTime>1633423215293</startTime><endTime>1633428963975</endTime><participants>43</participants><rawSize>661041513</rawSize><metadata><bbb-origin-version>v2-a8e12df</bbb-origin-version><meetingName>Семинар ИВТ 16-00</meetingName><meetingId>r3za1pj6yh6fliywgdozrwfqesdfq7g5vjn00sbu</meetingId><gl-listed>false</gl-listed><bbb-origin>Greenlight</bbb-origin><isBreakout>false</isBreakout><bbb-origin-server-name>vcs-3.ict.sc</bbb-origin-server-name></metadata><size>276176348</size><playback><format><type>presentation</type><url>https://vcs-6.ict.nsc.ru/playback/presentation/2.3/4d7c4b3f965fc189d9c6cb8ab68b0b07550bfb03-1633423215293
              </url><processingTime>16902619</processingTime><length>72</length><size>276176348</size></format></playback><data/></recording><recording><recordID>37c8d0e83c429289a34173f15ecc33fe05b2aa96-1649730325430</recordID><meetingID>ewfsozr1hyeu4y9iru6hdw05qtcifv1tqhnjn2v8</meetingID><internalMeetingID>37c8d0e83c429289a34173f15ecc33fe05b2aa96-1649730325430</internalMeetingID><name>Информационные технологии в задачах филологии и компьютерной лингвистики</name><isBreakout>false</isBreakout><published>true</published><state>published</state><startTime>1649730325430</startTime><endTime>1649733924949</endTime><participants>16</participants><rawSize>299475414</rawSize><metadata><bbb-origin-version>v2-a8e12df</bbb-origin-version><meetingName>Информационные технологии в задачах филологии и компьютерной лингвистики</meetingName><meetingId>ewfsozr1hyeu4y9iru6hdw05qtcifv1tqhnjn2v8</meetingId><gl-listed>false</gl-listed><bbb-origin>Greenlight</bbb-origin><isBreakout>false</isBreakout><bbb-origin-server-name>vcs-6.ict.nsc.ru</bbb-origin-server-name></metadata><size>131797361</size><playback><format><type>presentation</type><url>https://vcs-6.ict.nsc.ru/playback/presentation/2.3/37c8d0e83c429289a34173f15ecc33fe05b2aa96-1649730325430</url><processingTime>975586</processingTime><length>52</length><size>131797361</size></format></playback><data/></recording><recording><recordID>4d7c4b3f965fc189d9c6cb8ab68b0b07550bfb03-1699343312797</recordID><meetingID>r3za1pj6yh6fliywgdozrwfqesdfq7g5vjn00sbu</meetingID><internalMeetingID>4d7c4b3f965fc189d9c6cb8ab68b0b07550bfb03-1699343312797</internalMeetingID><name>Семинар ИВТ 16-00</name><isBreakout>false</isBreakout><published>true</published><state>published</state><startTime>1699343312797</startTime><endTime>1699351948986</endTime><participants>16</participants><rawSize>464657241</rawSize><metadata><bbb-recording-ready-url>https://vcs-6.ict.nsc.ru/recording_ready</bbb-recording-ready-url><bbb-origin-version>3</bbb-origin-version><endcallbackurl>https://vcs-6.ict.nsc.ru/meeting_ended</endcallbackurl><meetingName>Семинар ИВТ 16-00</meetingName><meetingId>r3za1pj6yh6fliywgdozrwfqesdfq7g5vjn00sbu</meetingId><bbb-origin>greenlight</bbb-origin><isBreakout>false</isBreakout></metadata><breakout><parentId>unknown</parentId><sequence>0</sequence><freeJoin>false</freeJoin></breakout><size>236750952</size><playback><format><type>presentation</type><url>http://vcs-6.ict.nsc.ru/playback/presentation/2.3/4d7c4b3f965fc189d9c6cb8ab68b0b07550bfb03-1699343312797</url><processingTime>537523</processingTime><length>70</length><size>236750952</size></format></playback><data/></recording><recording><recordID>69bb7bfe2cee6eba1805171a18616d4e99564df2-1681485100714</recordID><meetingID>02444f3035334cf9f81464e18c02bcbe0f1f2a1f</meetingID><internalMeetingID>69bb7bfe2cee6eba1805171a18616d4e99564df2-1681485100714</internalMeetingID><name>test3 room</name><isBreakout>false</isBreakout><published>true</published><state>published</state><startTime>1681485100714</startTime><endTime>1681485357818</endTime><participants>4</participants><rawSize>2426889</rawSize><metadata><bbb-origin-version>v2-a8e12df</bbb-origin-version><meetingName>test3 room</meetingName><meetingId>02444f3035334cf9f81464e18c02bcbe0f1f2a1f</meetingId><gl-listed>false</gl-listed><bbb-origin>Greenlight</bbb-origin><isBreakout>false</isBreakout><bbb-origin-server-name>vcs-3.ict.sbras.ru</bbb-origin-server-name></metadata><size>2648071</size><playback><format><type>presentation</type><url>https://vcs-6.ict.nsc.ru/playback/presentation/2.3/69bb7bfe2cee6eba1805171a18616d4e99564df2-1681485100714</url><processingTime>19788</processingTime><length>4</length><size>2648071</size></format></playback><data/></recording><recording><recordID>caeaa151fe7743faa3d160ccb904deddc5b7d1cb-1679370759325</recordID><meetingID>d0d1c7b449e81c35c1efae18607d2787f324fede</meetingID><internalMeetingID>caeaa151fe7743faa3d160ccb904deddc5b7d1cb-1679370759325</internalMeetingID><name>Семинар 11:00</name><isBreakout>false</isBreakout><published>true</published><state>published</state><startTime>1679370759325</startTime><endTime>1679383314344</endTime><participants>8</participants><rawSize>299792277</rawSize><metadata><bbb-origin-version>v2-a8e12df</bbb-origin-version><meetingName>Семинар 11:00</meetingName><meetingId>d0d1c7b449e81c35c1efae18607d2787f324fede</meetingId><gl-listed>false</gl-listed><bbb-origin>Greenlight</bbb-origin><isBreakout>false</isBreakout><bbb-origin-server-name>vcs-6.ict.nsc.ru</bbb-origin-server-name></metadata><size>59429301</size><playback><format><type>presentation</type><url>https://vcs-6.ict.nsc.ru/playback/presentation/2.3/caeaa151fe7743faa3d160ccb904deddc5b7d1cb-1679370759325</url><processingTime>352535</processingTime><length>21</length><size>59429301</size></format></playback><data/></recording><recording><recordID>efbfa7268ec7f78c80cc24e8924daa5277d72b1b-1694577743898</recordID><meetingID>xxr2xzmnj4h8omffvgm62sh5cn8ss2udfn1034k4</meetingID><internalMeetingID>efbfa7268ec7f78c80cc24e8924daa5277d72b1b-1694577743898</internalMeetingID><name>Голопапа Денис Юрьевич (ФИЦ ИВТ)</name><isBreakout>false</isBreakout><published>true</published><state>published</state><startTime>1694577743898</startTime><endTime>1694580848914</endTime><participants>3</participants><rawSize>4152931</rawSize><metadata><bbb-recording-ready-url>https://vcs-6.ict.nsc.ru/recording_ready</bbb-recording-ready-url><bbb-origin-version>3</bbb-origin-version><endcallbackurl>https://vcs-6.ict.nsc.ru/meeting_ended</endcallbackurl><meetingName>Голопапа Денис Юрьевич (ФИЦ ИВТ)</meetingName><meetingId>xxr2xzmnj4h8omffvgm62sh5cn8ss2udfn1034k4</meetingId><bbb-origin>greenlight</bbb-origin><isBreakout>false</isBreakout></metadata><breakout><parentId>unknown</parentId><sequence>0</sequence><freeJoin>false</freeJoin></breakout><size>4224867</size><playback><format><type>presentation</type><url>http://vcs-6.ict.nsc.ru/playback/presentation/2.3/efbfa7268ec7f78c80cc24e8924daa5277d72b1b-1694577743898</url><processingTime>25698</processingTime><length>6</length><size>4224867</size></format></playback><data/></recording></recordings>
            <totalElements>372</totalElements></response>
            """
        self.content_error = \
        """
            <response>
            <returncode>FAILED</returncode>
            <messageKey>checksumError</messageKey>
            <message>You did not pass the checksum security check</message>
            </response>
        """

        tree = etree.fromstring(self.content)
        recordings_xml = tree.find("recordings")
        self.one_recording = recordings_xml[0]

        tree2 = etree.fromstring(self.content_error)
        self.xml_test = tree2

    def test_request_records(self):
        url = "https://vcs-3.ict.sbras.ru/bigbluebutton/api/getRecordings?limit=7&offset=2"
        res = request_recordings(url)
        self.assertTrue(res)

    def test_request_records_incorrect_url(self):
        url = "https://vcs-3.i/dasd/"
        res = request_recordings(url)
        self.assertFalse(res)

    def test_is_xml_element_and_not_none(self):
        res = is_xml_element_or_not_none(self.xml_test)
        self.assertTrue(res)

    def test_is_xml_element_or_none(self):
        res = is_xml_element_or_not_none(self.xml_test)
        self.assertTrue(res)

    def test_parse_xml_recordings(self):
        res = parse_xml_recordings(self.content)

        self.assertEqual(type(res), dict)

        recordings = res.get("recordings")
        type_recordings = res.get("type_recordings")

        self.assertTrue(recordings)
        self.assertTrue(type_recordings)

        self.assertEqual(len(recordings), 7)
        self.assertEqual(len(type_recordings), 7)

        self.assertEqual(type(recordings[0]), tuple)
        self.assertEqual(type(recordings[0][1]), RecordingModel)
        self.assertEqual(type(type_recordings[0]), TypeRecordingModel)

    def test_parse_xml_recordings_input_none(self):
        res = parse_xml_recordings(None)
        self.assertIsNone(res)

    def test_parse_xml_recordings_input_xml_test(self):
        res = parse_xml_recordings(self.xml_test)
        self.assertIsNone(res)

    def test_parse_xml_recordings_input_str(self):
        res = parse_xml_recordings(self.content_error)
        self.assertIsNone(res)

    def test_parse_xml_type_recording(self):
        res = parse_xml_type_recording(self.one_recording)
        self.assertEqual(type(res), TypeRecordingModel)

    def test_parse_xml_type_recording_input_none(self):
        res = parse_xml_type_recording(None)
        self.assertIsNone(res)

    def test_parse_xml_type_recording_input_xml_test(self):
        res = parse_xml_type_recording(self.xml_test)
        self.assertIsNone(res)

    def test_parse_xml_type_recording_input_str(self):
        res = parse_xml_type_recording(self.content_error)
        self.assertIsNone(res)

    def test_parse_xml_recording(self):
        res = parse_xml_recording(self.one_recording)
        self.assertEqual(type(res), RecordingModel)

    def test_parse_xml_recording_input_none(self):
        res = parse_xml_recording(None)
        self.assertIsNone(res)

    def test_parse_xml_recording_input_xml_test(self):
        res = parse_xml_recording(self.xml_test)
        self.assertIsNone(res)

    def test_parse_xml_recording_input_str(self):
        res = parse_xml_recording(self.content_error)
        self.assertIsNone(res)

    def test_upload_recordings(self):
        recordings = parse_xml_recordings(self.content)
        self.assertIsNotNone(recordings)

        res = upload_recordings_to_db(recordings)
        self.assertIsNotNone(res)

        tm = TypeRecordingModel.objects.all()
        self.assertEqual(len(tm), 5)

        tm = RecordingModel.objects.all()
        self.assertEqual(len(tm), 7)

    def test_get_type_recordings(self):
        data = parse_xml_recordings(self.content)
        upload_recordings_to_db(data)

        type_recordings = get_type_recordings()
        self.assertEqual(len(type_recordings), 5)

    def test_get_type_recordings_to_dict(self):
        data = parse_xml_recordings(self.content)
        upload_recordings_to_db(data)

        type_recordings = get_type_recordings_to_dict()
        self.assertEqual(len(type_recordings), 5)

        res = [type_recording for type_recording in type_recordings]
        expected = [{'id': 5, 'name': 'test3 room'}, {'id': 7, 'name': 'Голопапа Денис Юрьевич (ФИЦ ИВТ)'}, {'id': 1, 'name': 'Информационные технологии в задачах филологии и компьютерной лингвистики'}, {'id': 6, 'name': 'Семинар 11:00'}, {'id': 2, 'name': 'Семинар ИВТ 16-00'}]

        self.assertEqual(res, expected)

    def test_upload_from_source(self):
        res = upload_from_source("vcs-3.ict.sbras.ru")
        self.assertIsNotNone(res)

        recordings_len = RecordingModel.objects.count()
        self.assertEqual(recordings_len, 372)

    def test_upload_empty_recordings(self):
        res = upload_from_source("vcs-3.ict.sbras.ru")
        self.assertIsNotNone(res)

        recordings_len = RecordingModel.objects.count()
        self.assertEqual(recordings_len, 372)

        res = upload_from_source("vcs-6.ict.nsc.ru")
        self.assertIsNotNone(res)

        recordings_len = RecordingModel.objects.count()
        self.assertIsNotNone(None)
        self.assertGreaterEqual(recordings_len, 570)

    def test_get_recordings_foreinkey_type_recording_by_name(self):
        data = parse_xml_recordings(self.content)
        upload_recordings_to_db(data)

        name = "Информационные технологии в задачах филологии и компьютерной лингвистики"
        recordings = get_recordings_foreinkey_type_recording(type_recording__name=name)

        self.assertEqual(len(recordings), 2)
        self.assertEqual(recordings[0].type_recording.name, name)

    def test_get_recordings_foreinkey_type_recording_by_id(self):
        data = parse_xml_recordings(self.content)
        upload_recordings_to_db(data)

        pk = 1
        recordings = get_recordings_foreinkey_type_recording(type_recording__id=pk)

        self.assertEqual(len(recordings), 2)
        self.assertEqual(recordings[0].type_recording.id, pk)

    def test_get_recordings_foreinkey_type_recording_to_dict_by_id(self):
        data = parse_xml_recordings(self.content)
        upload_recordings_to_db(data)

        pk = 1
        recordings = get_recordings_to_dict(
            fields=["record_id", "datetime_created", "datetime_stopped", "status"],
            filter_query=Q(type_recording__id=pk)
        )

        self.assertEqual(len(recordings), 2)

        recordings_dict = [item for item in recordings]

        res = [{
            'record_id': '37c8d0e83c429289a34173f15ecc33fe05b2aa96-1649730325430',
            'datetime_created': datetime.datetime(2022, 4, 12, 2, 25, 25, 430000, tzinfo=datetime.timezone.utc),
            'datetime_stopped': datetime.datetime(2022, 4, 12, 3, 25, 24, 949000, tzinfo=datetime.timezone.utc),
            'status': 1
        }, {
            'record_id': '37c8d0e83c429289a34173f15ecc33fe05b2aa96-1676974666046',
            'datetime_created': datetime.datetime(2023, 2, 21, 10, 17, 46, 46000, tzinfo=datetime.timezone.utc),
            'datetime_stopped': datetime.datetime(2023, 2, 21, 11, 26, 11, 753000, tzinfo=datetime.timezone.utc),
            'status': 1
        }]
        self.assertEqual(recordings_dict, res)

    def test_get_recordings_by_list_recording_ids(self):
        data = parse_xml_recordings(self.content)
        upload_recordings_to_db(data)

        recordings = get_recordings_foreinkey_type_recording(record_id__in=[
            "37c8d0e83c429289a34173f15ecc33fe05b2aa96-1676974666046",
            "4d7c4b3f965fc189d9c6cb8ab68b0b07550bfb03-1633423215293"
        ])

        self.assertEqual(len(recordings), 2)

    def test_update_recordings_fields(self):
        data = parse_xml_recordings(self.content)
        self.assertIsNotNone(data)

        for recording in data["recordings"]:
            recording[1].url = ''

        res = upload_recordings_to_db(data)
        self.assertIsNotNone(res)

        recordings_filter = list(filter(lambda x: x.url != '', RecordingModel.objects.all()))
        self.assertEqual(recordings_filter, [])

        test_recordings_dict = [
            {'record_id': '37c8d0e83c429289a34173f15ecc33fe05b2aa96-1676974666046',
             'meeting_id': 'ewfsozr1hyeu4y9iru6hdw05qtcifv1tqhnjn2v8',
             'datetime_created': datetime.datetime(2023, 2, 21, 10, 17, 46, 46000, tzinfo=datetime.timezone.utc),
             'datetime_stopped': datetime.datetime(2023, 2, 21, 11, 26, 11, 753000, tzinfo=datetime.timezone.utc),
             'type_recording': None, 'status': 1,
             'url': 'https://vcs-6.ict.nsc.ru/playback/presentation/2.3/37c8d0e83c429289a34173f15ecc33fe05b2aa96-1676974666046'},
            {'record_id': '4d7c4b3f965fc189d9c6cb8ab68b0b07550bfb03-1633423215293',
             'meeting_id': 'r3za1pj6yh6fliywgdozrwfqesdfq7g5vjn00sbu',
             'datetime_created': datetime.datetime(2021, 10, 5, 8, 40, 15, 293000, tzinfo=datetime.timezone.utc),
             'datetime_stopped': datetime.datetime(2021, 10, 5, 10, 16, 3, 975000, tzinfo=datetime.timezone.utc),
             'type_recording': None, 'status': 1,
             'url': 'https://vcs-6.ict.nsc.ru/playback/presentation/2.3/4d7c4b3f965fc189d9c6cb8ab68b0b07550bfb03-1633423215293'}
        ]
        test_recordings = [RecordingModel(**item) for item in test_recordings_dict]

        update_recordings_fields(test_recordings, ["url"])

        recordings_filter = list(filter(lambda x: x.url != '', RecordingModel.objects.all()))
        self.assertEqual(len(recordings_filter), 2)

    def test_upload_recordings_and_update_fields(self):
        upload_recordings_and_update_fields()

    def test_get_recording(self):
        recording = parse_xml_recording(self.one_recording)
        type_recording = parse_xml_type_recording(self.one_recording)
        data = {
            "recordings": [(type_recording.name, recording)],
            "type_recordings": [type_recording]
        }
        upload_recordings_to_db(data)

        requested_recoding = get_recording(recording.record_id)
        self.assertIsNotNone(requested_recoding)
        self.assertEqual(requested_recoding.record_id, recording.record_id)

    def test_get_recording_none(self):
        recording = parse_xml_recording(self.one_recording)

        requested_recoding = get_recording(recording.record_id)
        self.assertIsNone(requested_recoding)

    def test_update_recording_by_record_id(self):
        recording = parse_xml_recording(self.one_recording)
        type_recording = parse_xml_type_recording(self.one_recording)
        data = {
            "recordings": [(type_recording.name, recording)],
            "type_recordings": [type_recording]
        }
        upload_recordings_to_db(data)

        update_recording_by_record_id(recording.record_id, status=2)
        updated_recording = get_recording(recording.record_id)
        self.assertIsNotNone(updated_recording)
        self.assertEqual(updated_recording.status, 2)

    def test_update_recordings(self):
        data = parse_xml_recordings(self.content)
        self.assertIsNotNone(data)

        for recording in data["recordings"]:
            recording[1].url = ''

        res = upload_recordings_to_db(data)
        self.assertIsNotNone(res)
        recording_ids = [item.record_id for item in RecordingModel.objects.all()[:2]]
        update_recordings(Q(record_id__in=recording_ids), status=2)

        pending_recordings = RecordingModel.objects.filter(status=2)

        self.assertEqual(len(pending_recordings), 2)


class RecordingIdValidatorTests(TestCase):
    def test_validate_recording_id(self):
        record_id = "0293632817cdbb56991efab552bc1d1988f0cbca-1756431910931"
        res = validate_recording_id(record_id)
        self.assertIsNone(res)

    def test_validate_recording_id_incorrect(self):
        record_id = "0293632817cdbb56991efab552bc1d1988f0cbca-1756431910931a"
        self.assertRaises(ValidationError, validate_recording_id, record_id)


class RecordingIdFormTests(TestCase):
    def test_process_recordings_form(self):
        d = {
            "recording_ids": "0293632817cdbb56991efab552bc1d1988f0cbca-1756431910931,0293632817cdbb56991efab552bc1d1988f0cbca-1756347042103,0293632817cdbb56991efab552bc1d1988f0cbca-1756260131171,0293632817cdbb56991efab552bc1d1988f0cbca-1756172730700"
        }
        form = ProcessRecordingsForm(d)

        res = form.is_valid()
        self.assertTrue(res)


class RecordingTaskTests(TestCase):
    def setUp(self):
        self.content = \
            """
            <response>
              <returncode>SUCCESS</returncode>
              <recordings><recording><recordID>37c8d0e83c429289a34173f15ecc33fe05b2aa96-1676974666046</recordID><meetingID>ewfsozr1hyeu4y9iru6hdw05qtcifv1tqhnjn2v8</meetingID><internalMeetingID>37c8d0e83c429289a34173f15ecc33fe05b2aa96-1676974666046</internalMeetingID><name>Информационные технологии в задачах филологии и компьютерной лингвистики</name><isBreakout>false</isBreakout><published>true</published><state>published</state><startTime>1676974666046</startTime><endTime>1676978771753</endTime><participants>15</participants><rawSize>345908205</rawSize><metadata><bbb-origin-version>v2-a8e12df</bbb-origin-version><meetingName>Информационные технологии в задачах филологии и компьютерной лингвистики</meetingName><meetingId>ewfsozr1hyeu4y9iru6hdw05qtcifv1tqhnjn2v8</meetingId><gl-listed>false</gl-listed><bbb-origin>Greenlight</bbb-origin><isBreakout>false</isBreakout><bbb-origin-server-name>vcs-6.ict.nsc.ru</bbb-origin-server-name></metadata><size>175740599</size><playback><format><type>presentation</type><url>https://vcs-6.ict.nsc.ru/playback/presentation/2.3/37c8d0e83c429289a34173f15ecc33fe05b2aa96-1676974666046</url><processingTime>996111</processingTime><length>50</length><size>175740599</size></format></playback><data/></recording><recording><recordID>4d7c4b3f965fc189d9c6cb8ab68b0b07550bfb03-1633423215293</recordID><meetingID>r3za1pj6yh6fliywgdozrwfqesdfq7g5vjn00sbu</meetingID><internalMeetingID>4d7c4b3f965fc189d9c6cb8ab68b0b07550bfb03-1633423215293</internalMeetingID><name>Семинар ИВТ 16-00</name><isBreakout>false</isBreakout><published>true</published><state>published</state><startTime>1633423215293</startTime><endTime>1633428963975</endTime><participants>43</participants><rawSize>661041513</rawSize><metadata><bbb-origin-version>v2-a8e12df</bbb-origin-version><meetingName>Семинар ИВТ 16-00</meetingName><meetingId>r3za1pj6yh6fliywgdozrwfqesdfq7g5vjn00sbu</meetingId><gl-listed>false</gl-listed><bbb-origin>Greenlight</bbb-origin><isBreakout>false</isBreakout><bbb-origin-server-name>vcs-3.ict.sc</bbb-origin-server-name></metadata><size>276176348</size><playback><format><type>presentation</type><url>https://vcs-6.ict.nsc.ru/playback/presentation/2.3/4d7c4b3f965fc189d9c6cb8ab68b0b07550bfb03-1633423215293
              </url><processingTime>16902619</processingTime><length>72</length><size>276176348</size></format></playback><data/></recording><recording><recordID>37c8d0e83c429289a34173f15ecc33fe05b2aa96-1649730325430</recordID><meetingID>ewfsozr1hyeu4y9iru6hdw05qtcifv1tqhnjn2v8</meetingID><internalMeetingID>37c8d0e83c429289a34173f15ecc33fe05b2aa96-1649730325430</internalMeetingID><name>Информационные технологии в задачах филологии и компьютерной лингвистики</name><isBreakout>false</isBreakout><published>true</published><state>published</state><startTime>1649730325430</startTime><endTime>1649733924949</endTime><participants>16</participants><rawSize>299475414</rawSize><metadata><bbb-origin-version>v2-a8e12df</bbb-origin-version><meetingName>Информационные технологии в задачах филологии и компьютерной лингвистики</meetingName><meetingId>ewfsozr1hyeu4y9iru6hdw05qtcifv1tqhnjn2v8</meetingId><gl-listed>false</gl-listed><bbb-origin>Greenlight</bbb-origin><isBreakout>false</isBreakout><bbb-origin-server-name>vcs-6.ict.nsc.ru</bbb-origin-server-name></metadata><size>131797361</size><playback><format><type>presentation</type><url>https://vcs-6.ict.nsc.ru/playback/presentation/2.3/37c8d0e83c429289a34173f15ecc33fe05b2aa96-1649730325430</url><processingTime>975586</processingTime><length>52</length><size>131797361</size></format></playback><data/></recording><recording><recordID>4d7c4b3f965fc189d9c6cb8ab68b0b07550bfb03-1699343312797</recordID><meetingID>r3za1pj6yh6fliywgdozrwfqesdfq7g5vjn00sbu</meetingID><internalMeetingID>4d7c4b3f965fc189d9c6cb8ab68b0b07550bfb03-1699343312797</internalMeetingID><name>Семинар ИВТ 16-00</name><isBreakout>false</isBreakout><published>true</published><state>published</state><startTime>1699343312797</startTime><endTime>1699351948986</endTime><participants>16</participants><rawSize>464657241</rawSize><metadata><bbb-recording-ready-url>https://vcs-6.ict.nsc.ru/recording_ready</bbb-recording-ready-url><bbb-origin-version>3</bbb-origin-version><endcallbackurl>https://vcs-6.ict.nsc.ru/meeting_ended</endcallbackurl><meetingName>Семинар ИВТ 16-00</meetingName><meetingId>r3za1pj6yh6fliywgdozrwfqesdfq7g5vjn00sbu</meetingId><bbb-origin>greenlight</bbb-origin><isBreakout>false</isBreakout></metadata><breakout><parentId>unknown</parentId><sequence>0</sequence><freeJoin>false</freeJoin></breakout><size>236750952</size><playback><format><type>presentation</type><url>http://vcs-6.ict.nsc.ru/playback/presentation/2.3/4d7c4b3f965fc189d9c6cb8ab68b0b07550bfb03-1699343312797</url><processingTime>537523</processingTime><length>70</length><size>236750952</size></format></playback><data/></recording><recording><recordID>69bb7bfe2cee6eba1805171a18616d4e99564df2-1681485100714</recordID><meetingID>02444f3035334cf9f81464e18c02bcbe0f1f2a1f</meetingID><internalMeetingID>69bb7bfe2cee6eba1805171a18616d4e99564df2-1681485100714</internalMeetingID><name>test3 room</name><isBreakout>false</isBreakout><published>true</published><state>published</state><startTime>1681485100714</startTime><endTime>1681485357818</endTime><participants>4</participants><rawSize>2426889</rawSize><metadata><bbb-origin-version>v2-a8e12df</bbb-origin-version><meetingName>test3 room</meetingName><meetingId>02444f3035334cf9f81464e18c02bcbe0f1f2a1f</meetingId><gl-listed>false</gl-listed><bbb-origin>Greenlight</bbb-origin><isBreakout>false</isBreakout><bbb-origin-server-name>vcs-3.ict.sbras.ru</bbb-origin-server-name></metadata><size>2648071</size><playback><format><type>presentation</type><url>https://vcs-6.ict.nsc.ru/playback/presentation/2.3/69bb7bfe2cee6eba1805171a18616d4e99564df2-1681485100714</url><processingTime>19788</processingTime><length>4</length><size>2648071</size></format></playback><data/></recording><recording><recordID>caeaa151fe7743faa3d160ccb904deddc5b7d1cb-1679370759325</recordID><meetingID>d0d1c7b449e81c35c1efae18607d2787f324fede</meetingID><internalMeetingID>caeaa151fe7743faa3d160ccb904deddc5b7d1cb-1679370759325</internalMeetingID><name>Семинар 11:00</name><isBreakout>false</isBreakout><published>true</published><state>published</state><startTime>1679370759325</startTime><endTime>1679383314344</endTime><participants>8</participants><rawSize>299792277</rawSize><metadata><bbb-origin-version>v2-a8e12df</bbb-origin-version><meetingName>Семинар 11:00</meetingName><meetingId>d0d1c7b449e81c35c1efae18607d2787f324fede</meetingId><gl-listed>false</gl-listed><bbb-origin>Greenlight</bbb-origin><isBreakout>false</isBreakout><bbb-origin-server-name>vcs-6.ict.nsc.ru</bbb-origin-server-name></metadata><size>59429301</size><playback><format><type>presentation</type><url>https://vcs-6.ict.nsc.ru/playback/presentation/2.3/caeaa151fe7743faa3d160ccb904deddc5b7d1cb-1679370759325</url><processingTime>352535</processingTime><length>21</length><size>59429301</size></format></playback><data/></recording><recording><recordID>efbfa7268ec7f78c80cc24e8924daa5277d72b1b-1694577743898</recordID><meetingID>xxr2xzmnj4h8omffvgm62sh5cn8ss2udfn1034k4</meetingID><internalMeetingID>efbfa7268ec7f78c80cc24e8924daa5277d72b1b-1694577743898</internalMeetingID><name>Голопапа Денис Юрьевич (ФИЦ ИВТ)</name><isBreakout>false</isBreakout><published>true</published><state>published</state><startTime>1694577743898</startTime><endTime>1694580848914</endTime><participants>3</participants><rawSize>4152931</rawSize><metadata><bbb-recording-ready-url>https://vcs-6.ict.nsc.ru/recording_ready</bbb-recording-ready-url><bbb-origin-version>3</bbb-origin-version><endcallbackurl>https://vcs-6.ict.nsc.ru/meeting_ended</endcallbackurl><meetingName>Голопапа Денис Юрьевич (ФИЦ ИВТ)</meetingName><meetingId>xxr2xzmnj4h8omffvgm62sh5cn8ss2udfn1034k4</meetingId><bbb-origin>greenlight</bbb-origin><isBreakout>false</isBreakout></metadata><breakout><parentId>unknown</parentId><sequence>0</sequence><freeJoin>false</freeJoin></breakout><size>4224867</size><playback><format><type>presentation</type><url>http://vcs-6.ict.nsc.ru/playback/presentation/2.3/efbfa7268ec7f78c80cc24e8924daa5277d72b1b-1694577743898</url><processingTime>25698</processingTime><length>6</length><size>4224867</size></format></playback><data/></recording></recordings>
            <totalElements>372</totalElements></response>
            """
        self.content_error = \
        """
            <response>
            <returncode>FAILED</returncode>
            <messageKey>checksumError</messageKey>
            <message>You did not pass the checksum security check</message>
            </response>
        """

        tree = etree.fromstring(self.content)
        recordings_xml = tree.find("recordings")
        self.one_recording = recordings_xml[0]

    def test_create_recording_task(self):
        recording = parse_xml_recording(self.one_recording)
        type_recording = parse_xml_type_recording(self.one_recording)
        data = {
            "recordings": [(type_recording.name, recording)],
            "type_recordings": [type_recording]
        }
        upload_recordings_to_db(data)
        tmp_recording = RecordingModel.objects.get(record_id=recording.record_id)

        uid = uuid.uuid4()
        create_recording_task(recording=tmp_recording, task_id=uid)

        meeting_task = RecordingTaskIdModel.objects.get(task_id=uid)
        self.assertEqual(meeting_task.task_id, str(uid))

    def test_delete_recording_tasks(self):
        recording = parse_xml_recording(self.one_recording)
        type_recording = parse_xml_type_recording(self.one_recording)
        data = {
            "recordings": [(type_recording.name, recording)],
            "type_recordings": [type_recording]
        }
        upload_recordings_to_db(data)
        tmp_recording = RecordingModel.objects.get(record_id=recording.record_id)

        uid = uuid.uuid4()
        create_recording_task(recording=tmp_recording, task_id=str(uid))

        meeting_task = RecordingTaskIdModel.objects.get(task_id=uid)
        self.assertEqual(meeting_task.task_id, str(uid))

        delete_recordings_tasks(Q(recording_id=tmp_recording.record_id))
        meeting_task = None
        try:
            meeting_task = RecordingTaskIdModel.objects.get(task_id=uid)
        except RecordingTaskIdModel.DoesNotExist:
            pass

        self.assertIsNone(meeting_task)

    def test_get_recording_tasks(self):
        data = parse_xml_recordings(self.content)
        self.assertIsNotNone(data)

        for recording in data["recordings"]:
            recording[1].url = ''

        res = upload_recordings_to_db(data)
        self.assertIsNotNone(res)

        tmp_recordings = RecordingModel.objects.all()[:2]

        tmp_recording_ids = [tmp_recording.record_id for tmp_recording in tmp_recordings]
        for r in tmp_recordings:
            uid = uuid.uuid4()
            create_recording_task(recording=r, task_id=str(uid))

        recording_tasks = get_recording_tasks(Q(recording_id__in=tmp_recording_ids))

        self.assertEqual(len(recording_tasks), 2)

    def test_update_recording_task(self):
        recording = parse_xml_recording(self.one_recording)
        type_recording = parse_xml_type_recording(self.one_recording)
        data = {
            "recordings": [(type_recording.name, recording)],
            "type_recordings": [type_recording]
        }
        upload_recordings_to_db(data)
        tmp_recording = RecordingModel.objects.get(record_id=recording.record_id)

        uid = uuid.uuid4()
        create_recording_task(recording=tmp_recording, task_id=uid)

        meeting_task = RecordingTaskIdModel.objects.get(task_id=uid)
        self.assertIsNotNone(meeting_task)
        self.assertEqual(meeting_task.task_id, str(uid))

        uid = uuid.uuid4()
        update_recording_tasks(Q(recording_id=meeting_task.recording_id), task_id=uid)

        meeting_task = RecordingTaskIdModel.objects.get(task_id=uid)
        self.assertIsNotNone(meeting_task)
        self.assertEqual(meeting_task.task_id, str(uid))

    def test_create_recording_tasks(self):
        data = parse_xml_recordings(self.content)
        self.assertIsNotNone(data)

        res = upload_recordings_to_db(data)
        self.assertIsNotNone(res)

        tmp_recordings = RecordingModel.objects.all()[:3]

        l = []
        for r in tmp_recordings:
            uid = uuid.uuid4()
            l.append(RecordingTaskIdModel(recording=r, task_id=str(uid)))

        res = create_recording_tasks(l)
        self.assertIsNotNone(res)

        count = RecordingTaskIdModel.objects.count()

        self.assertEqual(count, 3)


class StartSubProcessTests(TestCase):
    def test_start_subprocess(self):
        resource = "vcs-6.ict.nsc.ru"
        recording_id = "c53d75df9d50c196f87e15ce56bd4f6f6235cc24-1666841342472"
        opid = subprocess.Popen(
            [
                "./common/start-repack-ffmpeg.sh",
                "-r", resource,
                "-i", recording_id,
                "-o", "files/ffmpeg"
            ],
            stdout=subprocess.DEVNULL
        )
        print(opid)
        self.assertIsNotNone(None)


class ProcessRecordingsAPIView(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
