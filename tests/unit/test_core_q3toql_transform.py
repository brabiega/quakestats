from quakestats.core.q3toql.transform import (
    Q3toQL,
)


class TestQ3toQL():
    def test_parse_user_info_changed(self):
        tf = Q3toQL()
        raw_data = r'4 n\n0npax\t\0\model\sarge\hmodel\sarge\c1\1\c2\5\hc\100\w\0\l\0\rt\0\st\0'  # noqa
        client_id, user_info = tf.parse_user_info_changed(raw_data)
        assert client_id == 4
        assert user_info['name'] == 'n0npax'
        assert user_info['team'] == 'FREE'
        assert user_info['model'] == 'sarge'
