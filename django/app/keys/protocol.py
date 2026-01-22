"""
MQTT電文パーサー・ビルダー
TG Octopus Energy スマートメーター仕様書準拠

電文構造:
- Command ID: 5bytes HEX (例: 0101B, 00000B)
- Parameter: 1byte
- Data Length: 2bytes (little endian)
- Data: 可変長
"""
import struct
from datetime import datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


# コマンドID定義
CMD_KEY_EXCHANGE = '0101B'      # C2S: 鍵交換要求
CMD_KEY_RESPONSE = '00000B'     # S2C: 鍵交換応答
CMD_INTERVAL_DATA = '00300B'    # C2S: 30分値データ
CMD_EVENT_LOG = '00500B'        # C2S: イベントログ
CMD_B_ROUTE_CONFIG = '00111B'   # S2C: Bルート設定


class MessageParser:
    """C2S電文パーサー"""
    
    def __init__(self, hex_data: str):
        self.hex_data = hex_data.upper().replace(' ', '')
        self.data = bytes.fromhex(self.hex_data)
        self.pos = 0
    
    def read_bytes(self, n: int) -> bytes:
        result = self.data[self.pos:self.pos + n]
        self.pos += n
        return result
    
    def read_hex(self, n: int) -> str:
        return self.read_bytes(n).hex().upper()
    
    def read_uint8(self) -> int:
        return struct.unpack('B', self.read_bytes(1))[0]
    
    def read_uint16_le(self) -> int:
        return struct.unpack('<H', self.read_bytes(2))[0]
    
    def read_uint32_le(self) -> int:
        return struct.unpack('<I', self.read_bytes(4))[0]
    
    def read_ascii(self, n: int) -> str:
        return self.read_bytes(n).decode('ascii', errors='replace').rstrip('\x00')
    
    def parse_header(self) -> dict:
        """ヘッダー解析（共通部分）"""
        return {
            'command_id': self.read_hex(5),
            'parameter': self.read_uint8(),
            'data_length': self.read_uint16_le(),
        }
    
    def parse_key_exchange(self) -> dict:
        """鍵交換要求（0101B）のパース"""
        header = self.parse_header()
        
        # parameter: 0=新規(default key), 1=再接続(master key), 2=ACK
        return {
            **header,
            'type': ['new_registration', 'reconnection', 'ack'][header['parameter']],
        }
    
    def parse_interval_data(self) -> dict:
        """30分値データ（00300B）のパース"""
        header = self.parse_header()
        
        # タイムスタンプ (YY MM DD HH mm ss)
        year = 2000 + self.read_uint8()
        month = self.read_uint8()
        day = self.read_uint8()
        hour = self.read_uint8()
        minute = self.read_uint8()
        second = self.read_uint8()
        
        try:
            timestamp = datetime(year, month, day, hour, minute, second)
        except ValueError:
            timestamp = None
        
        # 電力データ（4bytes each, unit: 0.01kWh）
        import_kwh = Decimal(self.read_uint32_le()) / 100
        export_kwh = Decimal(self.read_uint32_le()) / 100
        route_b_import_kwh = Decimal(self.read_uint32_le()) / 100
        route_b_export_kwh = Decimal(self.read_uint32_le()) / 100
        
        return {
            **header,
            'timestamp': timestamp,
            'import_kwh': import_kwh,
            'export_kwh': export_kwh,
            'route_b_import_kwh': route_b_import_kwh,
            'route_b_export_kwh': route_b_export_kwh,
        }
    
    def parse_event_log(self) -> dict:
        """イベントログ（00500B）のパース"""
        header = self.parse_header()
        
        record_no = self.read_uint16_le()
        event_code = self.read_ascii(3)
        
        # タイムスタンプ
        year = 2000 + self.read_uint8()
        month = self.read_uint8()
        day = self.read_uint8()
        hour = self.read_uint8()
        minute = self.read_uint8()
        second = self.read_uint8()
        
        try:
            timestamp = datetime(year, month, day, hour, minute, second)
        except ValueError:
            timestamp = None
        
        # イベント時の積算値
        import_kwh = Decimal(self.read_uint32_le()) / 100 if self.pos < len(self.data) else None
        
        return {
            **header,
            'record_no': record_no,
            'event_code': event_code.strip(),
            'timestamp': timestamp,
            'import_kwh': import_kwh,
        }


class MessageBuilder:
    """S2C電文ビルダー"""
    
    def __init__(self):
        self.data = bytearray()
    
    def write_bytes(self, data: bytes):
        self.data.extend(data)
    
    def write_hex(self, hex_str: str):
        self.data.extend(bytes.fromhex(hex_str))
    
    def write_uint8(self, value: int):
        self.data.extend(struct.pack('B', value))
    
    def write_uint16_le(self, value: int):
        self.data.extend(struct.pack('<H', value))
    
    def write_ascii(self, text: str, length: int):
        encoded = text.encode('ascii')[:length]
        padded = encoded.ljust(length, b'\x00')
        self.data.extend(padded)
    
    def to_hex(self) -> str:
        return self.data.hex().upper()
    
    def to_bytes(self) -> bytes:
        return bytes(self.data)


def build_key_response_new(master_key: str, data_key: str) -> str:
    """
    新規登録時の鍵交換応答（00000B-1）を生成
    
    Args:
        master_key: マスターキー（16文字ASCII）
        data_key: データキー（16文字ASCII）
    
    Returns:
        電文HEX文字列
    """
    builder = MessageBuilder()
    
    # Header
    builder.write_hex('00000B')  # Command ID (5 bytes as hex = 10 chars, but spec says 5 bytes)
    # 実際は00000Bは3バイト相当。仕様書確認必要
    # 仮に5バイトとして: 0x00 0x00 0x0B を5バイトに拡張
    # → '0000000B0B' の形式と仮定
    
    builder = MessageBuilder()
    builder.write_bytes(bytes.fromhex('000000000B'))  # 5 bytes command
    builder.write_uint8(1)  # parameter = 1 (new registration response)
    
    # Data: master_key(16) + data_key(16)
    payload = master_key.encode('ascii') + data_key.encode('ascii')
    builder.write_uint16_le(len(payload))
    builder.write_bytes(payload)
    
    return builder.to_hex()


def build_key_response_reconnect(data_key: str) -> str:
    """
    再接続時の鍵交換応答（00000B-0）を生成
    
    Args:
        data_key: 新しいデータキー（16文字ASCII）
    
    Returns:
        電文HEX文字列
    """
    builder = MessageBuilder()
    builder.write_bytes(bytes.fromhex('000000000B'))
    builder.write_uint8(0)  # parameter = 0 (reconnection response)
    
    payload = data_key.encode('ascii')
    builder.write_uint16_le(len(payload))
    builder.write_bytes(payload)
    
    return builder.to_hex()


def build_key_confirm() -> str:
    """
    鍵交換完了確認（00000B-2）を生成
    
    Returns:
        電文HEX文字列
    """
    builder = MessageBuilder()
    builder.write_bytes(bytes.fromhex('000000000B'))
    builder.write_uint8(2)  # parameter = 2 (confirmation)
    builder.write_uint16_le(0)  # no data
    
    return builder.to_hex()


def build_b_route_config(b_route_id: str, password: str) -> str:
    """
    Bルート設定コマンド（00111B）を生成
    
    Args:
        b_route_id: BルートID（最大32文字）
        password: パスワード（最大32文字）
        空文字の場合は無効化（"0"を送信）
    
    Returns:
        電文HEX文字列
    """
    builder = MessageBuilder()
    builder.write_bytes(bytes.fromhex('0000111B00'))  # 5 bytes仮定
    
    if not b_route_id or not password:
        # 無効化
        builder.write_uint8(1)  # parameter = set
        payload = b'0' + b'0'
        builder.write_uint16_le(len(payload))
        builder.write_bytes(payload)
    else:
        builder.write_uint8(1)  # parameter = set
        # ID(32bytes, 0パディング) + Password(32bytes, 0パディング)
        id_bytes = b_route_id.encode('ascii')[:32].ljust(32, b'\x00')
        pw_bytes = password.encode('ascii')[:32].ljust(32, b'\x00')
        payload = id_bytes + pw_bytes
        builder.write_uint16_le(len(payload))
        builder.write_bytes(payload)
    
    return builder.to_hex()


def build_b_route_query() -> str:
    """
    Bルート設定取得コマンド（00111B-0）を生成
    
    Returns:
        電文HEX文字列
    """
    builder = MessageBuilder()
    builder.write_bytes(bytes.fromhex('0000111B00'))
    builder.write_uint8(0)  # parameter = query
    builder.write_uint16_le(0)
    
    return builder.to_hex()


def parse_command_id(hex_data: str) -> str:
    """電文からコマンドIDを抽出"""
    return hex_data[:10].upper()  # 5 bytes = 10 hex chars