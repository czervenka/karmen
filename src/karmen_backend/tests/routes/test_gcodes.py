import os
import io
import tempfile
import unittest
import mock

from server import app
from server.database import gcodes, printjobs

class ListRoute(unittest.TestCase):
    def setUp(self):
        self.gcode_ids = []
        self.gcode_ids.append(gcodes.add_gcode(
            path="a/b/c",
            filename="file1",
            display="file-display",
            absolute_path="/ab/a/b/c",
            size=123
        ))
        self.gcode_ids.append(gcodes.add_gcode(
            path="a/b/dc",
            filename="file2",
            display="file-display",
            absolute_path="/ab/a/b/c",
            size=123
        ))

    def test_list(self):
        with app.test_client() as c:
            response = c.get('/gcodes')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(len(response.json) >= 2)
            self.assertTrue("id" in response.json[0])
            self.assertTrue("path" in response.json[0])
            self.assertTrue("display" in response.json[0])
            self.assertTrue("absolute_path" in response.json[0])
            self.assertTrue("uploaded" in response.json[0])
            self.assertTrue("size" in response.json[0])
            self.assertTrue("data" in response.json[0])

class DetailRoute(unittest.TestCase):
    def setUp(self):
        self.gcode_id = gcodes.add_gcode(
            path="a/b/c",
            filename="file1",
            display="file-display",
            absolute_path="/ab/a/b/c",
            size=123
        )

    def test_detail(self):
        with app.test_client() as c:
            response = c.get('/gcodes/%s' % self.gcode_id)
            self.assertEqual(response.status_code, 200)
            self.assertTrue("id" in response.json)
            self.assertEqual(response.json["id"], self.gcode_id)

    def test_404(self):
        with app.test_client() as c:
            response = c.get('/gcodes/172.16')
            self.assertEqual(response.status_code, 404)

class CreateRoute(unittest.TestCase):
    @mock.patch("server.routes.gcodes.files.save", return_value={
        "path": "path",
        "filename": "filename",
        "display": "display",
        "absolute_path": "abspath",
        "size": 123
    })
    def test_upload(self, mocked_save):
        with app.test_client() as c:
            data = dict(
                file=(io.BytesIO(b'my file contents'), "some.gcode"),
            )
            response = c.post('/gcodes', data=data, content_type='multipart/form-data')
            self.assertEqual(response.status_code, 201)
            args, kwargs = mocked_save.call_args
            self.assertEqual(args[1], '/')

    @mock.patch("server.routes.gcodes.files.save", return_value={
        "path": "path",
        "filename": "filename",
        "display": "display",
        "absolute_path": "abspath",
        "size": 123
    })
    def test_upload_path(self, mocked_save):
        with app.test_client() as c:
            data = dict(
                file=(io.BytesIO(b'my file contents'), "some.gcode"),
                path='/a/b'
            )
            response = c.post('/gcodes', data=data, content_type='multipart/form-data')
            self.assertEqual(response.status_code, 201)
            args, kwargs = mocked_save.call_args
            self.assertEqual(args[1], '/a/b')
            self.assertTrue("id" in response.json)
            self.assertTrue("path" in response.json)
            self.assertTrue("filename" in response.json)
            self.assertTrue("display" in response.json)
            self.assertTrue("absolute_path" in response.json)
            self.assertTrue("uploaded" in response.json)
            self.assertTrue("size" in response.json)

    @mock.patch("server.routes.gcodes.files.save")
    def test_upload_io_error(self, mocked_save):
        mocked_save.side_effect = IOError('Disk problem')
        with app.test_client() as c:
            data = dict(
                file=(io.BytesIO(b'my file contents'), "some.gcode"),
            )
            response = c.post('/gcodes', data=data, content_type='multipart/form-data')
            self.assertEqual(response.status_code, 500)

    def test_upload_no_file(self):
        with app.test_client() as c:
            response = c.post('/gcodes')
            self.assertEqual(response.status_code, 400)

    def test_upload_empty_file(self):
        with app.test_client() as c:
            data = dict(
                file=(io.BytesIO(b'my file contents'), ""),
            )
            response = c.post('/gcodes', data=data, content_type='multipart/form-data')
            self.assertEqual(response.status_code, 400)
    def test_upload_not_gcode(self):
        with app.test_client() as c:
            data = dict(
                file=(io.BytesIO(b'my file contents'), "some.txt"),
            )
            response = c.post('/gcodes', data=data, content_type='multipart/form-data')
            self.assertEqual(response.status_code, 415)

class DeleteRoute(unittest.TestCase):
    def test_delete(self):
        gcode_id = gcodes.add_gcode(
            path="a/b/c",
            filename="file1",
            display="file-display",
            absolute_path="/ab/a/b/c",
            size=123
        )
        printjobs.add_printjob(gcode_id=gcode_id, printer_ip="172.16.236.11:8080")
        printjobs.add_printjob(gcode_id=gcode_id, printer_ip="172.16.236.11:8080")
        with app.test_client() as c:
            response = c.delete('/gcodes/%s' % gcode_id)
            self.assertEqual(response.status_code, 204)
        self.assertEqual(gcodes.get_gcode(gcode_id), None)
        self.assertEqual([r for r in printjobs.get_printjobs() if r["gcode_id"] == gcode_id], [])

    def test_delete_unknown(self):
        with app.test_client() as c:
            response = c.delete('/gcodes/172.16')
            self.assertEqual(response.status_code, 404)

class GetDataRoute(unittest.TestCase):
    def test_download(self):
        mock_file = tempfile.NamedTemporaryFile(delete=False)
        gcode_id = gcodes.add_gcode(
            path="a/b/c",
            filename="file1",
            display="file-display",
            absolute_path=mock_file.name,
            size=123
        )
        with app.test_client() as c:
            response = c.get('/gcodes/%s/data' % gcode_id)
            self.assertEqual(response.status_code, 200)
        mock_file.close()
        os.remove(mock_file.name)

    def test_get_unknown(self):
        with app.test_client() as c:
            response = c.get('/gcodes/172.16/data')
            self.assertEqual(response.status_code, 404)

    def test_get_not_on_disk(self):
        gcode_id = gcodes.add_gcode(
            path="a/b/c",
            filename="file1",
            display="file-display",
            absolute_path="/ab/a/b/c",
            size=123
        )
        with app.test_client() as c:
            response = c.get('/gcodes/%s/data' % gcode_id)
            self.assertEqual(response.status_code, 404)