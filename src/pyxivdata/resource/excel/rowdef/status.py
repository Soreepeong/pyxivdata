import enum
import typing

from pyxivdata.escaped_string import SqEscapedString
from pyxivdata.resource.excel.reader import ExdRow
from pyxivdata.resource.excel.structures import ExhColumnDefinition


class StatusCategory(enum.IntEnum):
    Detrimental = 1
    Beneficial = 2


# https://github.com/xivapi/ffxiv-datamining/blob/master/csv/Status.csv
class StatusRow(ExdRow):
    name: SqEscapedString = 0
    description: SqEscapedString = 1
    icon: int = 2
    max_stacks: int = 3
    category: StatusCategory = 5
    lock_movement: bool = 8
    lock_action: bool = 10
    lock_control: bool = 11
    transfiguration: bool = 12
    can_dispel: bool = 14
    inflicted_by_actor: bool = 15
    is_permanent: bool = 16
    party_list_priority: int = 17
    amount: int = 21
    log: int = 24
    is_fc_buff: bool = 25
    invisibility: bool = 26

    def __init__(self, row_id: int, sub_row_id: typing.Optional[int],
                 columns: typing.Sequence[ExhColumnDefinition],
                 fixed_data: typing.Union[bytes, bytearray, memoryview],
                 variable_data: typing.Union[bytes, bytearray, memoryview]):
        super().__init__(row_id, sub_row_id, columns, fixed_data, variable_data)

    def __str__(self):
        return f"Status({self.row_id}: {self.name})"
