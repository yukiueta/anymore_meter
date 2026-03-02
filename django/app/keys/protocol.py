"""
MQTT電文パーサー・ビルダー
TG Octopus Energy スマートメーター仕様書準拠

C2S電文構造 (メーター→サーバ):
- Meter Status: 2bytes (bit#15-13: MeterType, bit#12-9: PacketType, bit#8-0: Status)
- Meter ID: 6bytes (BCD)
- Data: 可変長

S2C電文構造 (サーバ→メーター):
- Command Type: 1byte
- Meter ID: 6bytes
- Command Parameter: 可変長
"""
import struct
from datetime import datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


# パケットタイプ定義 (Meter Status bit#12-9)
PACKET_TYPE_INSTANT = 0b0001      # 瞬時値
PACKET_TYPE_INTERVAL = 0b0010     # 30分値
PACKET_TYPE_KEY_EXCHANGE = 0b0101 # 鍵交換
PACKET_TYPE_MULTI = 0b1010        # マルチパケット
PACKET_TYPE_EVENT = 0b1011        # イベントログ


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
    
    def read_uint16_be(self) -> int:
        return struct.unpack('>H', self.read_bytes(2))[0]
    
    def read_uint32_le(self) -> int:
        return struct.unpack('<I', self.read_bytes(4))[0]
    
    def read_uint32_be(self) -> int:
        return struct.unpack('>I', self.read_bytes(4))[0]
    
    def read_ascii(self, n: int) -> str:
        return self.read_bytes(n).decode('ascii', errors='replace').rstrip('\x00')
    
    def read_bcd_meter_id(self) -> str:
        """6バイトBCDからメーターIDを読み取る"""
        raw = self.read_bytes(6)
        # BCD: 4A220004683F -> J220004683
        hex_str = raw.hex().upper()
        # 最初の1バイトがASCII文字コード
        first_char = chr(raw[0]) if 0x20 <= raw[0] <= 0x7F else '?'
        # 残りはBCD数字
        digits = hex_str[2:11]  # 220004683
        return first_char + digits
    
    def parse_header(self) -> dict:
        """C2Sヘッダー解析"""
        # Meter Status (2 bytes, big endian)
        meter_status = self.read_uint16_be()
        
        # Meter ID (6 bytes BCD)
        meter_id = self.read_bcd_meter_id()
        
        # パケットタイプ抽出 (bit#12-9)
        packet_type = (meter_status >> 9) & 0x0F
        
        # ステータスビット (bit#8-0)
        status_bits = meter_status & 0x1FF
        
        # 鍵交換の場合、次の1バイトがパラメータ
        parameter = None
        if packet_type == PACKET_TYPE_KEY_EXCHANGE:
            parameter = self.read_uint8()
        
        return {
            'meter_status': meter_status,
            'meter_id': meter_id,
            'packet_type': packet_type,
            'status_bits': status_bits,
            'parameter': parameter,
        }
    
    def parse_key_exchange(self) -> dict:
        """鍵交換要求のパース"""
        header = self.parse_header()
        
        param = header['parameter'] if header['parameter'] is not None else 0
        type_names = {0: 'new_registration', 1: 'reconnection', 2: 'ack'}
        
        return {
            **header,
            'parameter': param,
            'type': type_names.get(param, 'unknown'),
        }
    
    def parse_interval_data(self) -> dict:
        """30分値/瞬時値データのパース"""
        header = self.parse_header()
        
        # タイムスタンプ (Unix timestamp, 4 bytes, big endian)
        unix_ts = self.read_uint32_be()
        try:
            timestamp = datetime.fromtimestamp(unix_ts)
        except (ValueError, OSError):
            timestamp = None
        
        # 電力データ（4bytes each, big endian, unit: 0.01kWh）
        import_kwh = Decimal(self.read_uint32_be()) / 100
        export_kwh = Decimal(self.read_uint32_be()) / 100
        
        # Pulse count (4 bytes) - 通常は 0xFFFFFFFE
        pulse_count = self.read_uint32_be()
        
        # Route-B データ
        route_b_import_kwh = Decimal(self.read_uint32_be()) / 100
        route_b_export_kwh = Decimal(self.read_uint32_be()) / 100
        
        return {
            **header,
            'timestamp': timestamp,
            'import_kwh': import_kwh,
            'export_kwh': export_kwh,
            'pulse_count': pulse_count,
            'route_b_import_kwh': route_b_import_kwh,
            'route_b_export_kwh': route_b_export_kwh,
        }
    
    def parse_event_log(self) -> dict:
        """イベントログのパース"""
        header = self.parse_header()
        
        # Unix timestamp
        unix_ts = self.read_uint32_be()
        try:
            timestamp = datetime.fromtimestamp(unix_ts)
        except (ValueError, OSError):
            timestamp = None
        
        # Import energy
        import_kwh = Decimal(self.read_uint32_be()) / 100 if self.pos + 4 <= len(self.data) else None
        
        # Pulse count
        pulse_count = self.read_uint32_be() if self.pos + 4 <= len(self.data) else None
        
        # Record No (2 bytes)
        record_no = self.read_uint16_be() if self.pos + 2 <= len(self.data) else None
        
        # Event code (2 bytes)
        event_code_raw = self.read_uint16_be() if self.pos + 2 <= len(self.data) else None
        event_code = f"{event_code_raw:04X}" if event_code_raw else None
        
        return {
            **header,
            'timestamp': timestamp,
            'import_kwh': import_kwh,
            'pulse_count': pulse_count,
            'record_no': record_no,
            'event_code': event_code,
        }

    def parse_multi_interval(self) -> dict:
        """30分値マルチパケットのパース (1010b)
        
        仕様書P.21:
        Header(2bytes) + MeterID(6bytes) + DataType(1byte) + Count(1byte)
        + [UnixTS(4) + Import(4) + Export(4) + Pulse(4) + RB_Import(4) + RB_Export(4)] × N
        + 終端(000000000000)
        """
        header = self.parse_header()
        
        # Data type (1 byte): 0 = w/o voltage, 1 = w/ voltage
        data_type = self.read_uint8()
        
        # 繰り返し数 (1 byte)
        count = self.read_uint8()
        
        logger.info(f'Multi-interval: data_type={data_type}, count={count}')
        
        readings = []
        for i in range(count):
            if self.pos + 24 > len(self.data):
                break
            
            unix_ts = self.read_uint32_be()
            
            # 終端判定 (タイムスタンプが0)
            if unix_ts == 0:
                break
            
            try:
                timestamp = datetime.fromtimestamp(unix_ts)
            except (ValueError, OSError):
                timestamp = None
            
            import_kwh = Decimal(self.read_uint32_be()) / 100
            export_kwh = Decimal(self.read_uint32_be()) / 100
            pulse_count = self.read_uint32_be()
            route_b_import_kwh = Decimal(self.read_uint32_be()) / 100
            route_b_export_kwh = Decimal(self.read_uint32_be()) / 100
            
            readings.append({
                'timestamp': timestamp,
                'import_kwh': import_kwh,
                'export_kwh': export_kwh,
                'pulse_count': pulse_count,
                'route_b_import_kwh': route_b_import_kwh,
                'route_b_export_kwh': route_b_export_kwh,
            })
        
        return {
            **header,
            'data_type': data_type,
            'count': count,
            'readings': readings,
        }


def get_packet_type(hex_data: str) -> int:
    """電文からパケットタイプを抽出"""
    if len(hex_data) < 4:
        return -1
    meter_status = int(hex_data[:4], 16)
    return (meter_status >> 9) & 0x0F


def is_key_exchange(hex_data: str) -> bool:
    return get_packet_type(hex_data) == PACKET_TYPE_KEY_EXCHANGE


def is_interval_data(hex_data: str) -> bool:
    ptype = get_packet_type(hex_data)
    return ptype in (PACKET_TYPE_INSTANT, PACKET_TYPE_INTERVAL)


def is_event_log(hex_data: str) -> bool:
    return get_packet_type(hex_data) == PACKET_TYPE_EVENT


# ========== S2C電文ビルダー (変更なし) ==========

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


def encode_meter_id_bcd(meter_id: str) -> bytes:
    """メーターIDをBCD 6バイトにエンコード"""
    # 例: J239000046 -> 4A 23 90 00 04 6F
    if len(meter_id) < 2:
        return b'\x00' * 6
    
    first_char = meter_id[0].encode('ascii')  # 'J' -> 0x4A
    digits = meter_id[1:]  # '239000046'
    
    # 10桁に満たない場合は末尾に'F'を追加
    if len(digits) < 10:
        digits = digits + 'F' * (10 - len(digits))
    
    # 2桁ずつBCDに変換
    bcd_bytes = bytes([
        int(digits[0:2], 16),  # 23
        int(digits[2:4], 16),  # 90
        int(digits[4:6], 16),  # 00
        int(digits[6:8], 16),  # 04
        int(digits[8:10], 16), # 6F
    ])
    
    return first_char + bcd_bytes


def build_key_response_new(meter_id: str, master_key: str, data_key: str) -> str:
    """新規登録時の鍵交換応答を生成"""
    builder = MessageBuilder()
    
    # Command Type: class=001 (Power Meter), command=00000 (Key Exchange)
    # Bit#7-5: 001, Bit#4-0: 00000 -> 0x20
    builder.write_uint8(0x20)
    
    # Meter ID (6 bytes BCD)
    builder.write_bytes(encode_meter_id_bcd(meter_id))
    
    # Parameter: 1 = 新規登録応答
    builder.write_uint8(1)
    
    # Data: Master Key (16 bytes) + Data Key (16 bytes)
    payload = master_key.encode('ascii') + data_key.encode('ascii')
    
    # Data Length (1 byte)
    builder.write_uint8(len(payload))
    
    # Data
    builder.write_bytes(payload)
    
    remainder = len(builder.data) % 16
    if remainder != 0:
        builder.write_bytes(b'\x00' * (16 - remainder))
    
    return builder.to_hex()

def build_key_response_reconnect(meter_id: str, new_data_key: str) -> str:
    """再接続時の鍵交換応答を生成"""
    builder = MessageBuilder()
    
    # Command Type: class=001 (Power Meter), command=00000 (Key Exchange)
    builder.write_uint8(0x20)
    
    # Meter ID (6 bytes BCD)
    builder.write_bytes(encode_meter_id_bcd(meter_id))
    
    # Parameter: 0 = 再接続応答
    builder.write_uint8(0)
    
    # Data: Data Key (16 bytes) - Data Lengthなし
    payload = new_data_key.encode('ascii')
    builder.write_bytes(payload)
    
    remainder = len(builder.data) % 16
    if remainder != 0:
        builder.write_bytes(b'\x00' * (16 - remainder))
    
    return builder.to_hex()

def build_key_confirm(meter_id: str) -> str:
    """鍵交換完了確認を生成"""
    builder = MessageBuilder()
    
    # Command Type: class=001 (Power Meter), command=00000 (Key Exchange)
    builder.write_uint8(0x20)
    
    # Meter ID (6 bytes BCD)
    builder.write_bytes(encode_meter_id_bcd(meter_id))
    
    # Parameter: 2 = ACK - 追加データなし
    builder.write_uint8(2)
    
    remainder = len(builder.data) % 16
    if remainder != 0:
        builder.write_bytes(b'\x00' * (16 - remainder))
    
    return builder.to_hex()

def build_b_route_config(meter_id: str, b_route_id: str, password: str) -> str:
    """Bルート設定コマンドを生成"""
    builder = MessageBuilder()
    
    # Command Type: class=001 (Power Meter), command=00111 (B-route)
    # Bit#7-5: 001, Bit#4-0: 00111 -> 0x27
    builder.write_uint8(0x27)
    
    # Meter ID (6 bytes BCD)
    builder.write_bytes(encode_meter_id_bcd(meter_id))
    
    # Data: ID (32 bytes) + Password (up to 32 bytes)
    id_bytes = b_route_id.encode('ascii')[:32].ljust(32, b'\x00')
    pw_bytes = password.encode('ascii')[:32].ljust(32, b'\x00')
    payload = id_bytes + pw_bytes
    
    # Data length (1 byte)
    builder.write_uint8(len(payload))
    
    # Data
    builder.write_bytes(payload)
    
    remainder = len(builder.data) % 16
    if remainder != 0:
        builder.write_bytes(b'\x00' * (16 - remainder))
    
    return builder.to_hex()

def build_b_route_query() -> str:
    """Bルート設定取得コマンドを生成"""
    builder = MessageBuilder()
    builder.write_bytes(bytes.fromhex('0000111B00'))
    builder.write_uint8(0)
    builder.write_uint16_le(0)
    return builder.to_hex()