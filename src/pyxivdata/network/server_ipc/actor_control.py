import abc

from pyxivdata.network.server_ipc import *
from pyxivdata.network.enums import TargetMarkerType


class ActorControlBase(abc.ABC):
    TYPE: typing.ClassVar[ActorControlType]

    def __init__(self, data: IpcActorControlStub):
        self.data = data


class ActorControlAggro(ActorControlBase):
    TYPE = ActorControlType.Aggro

    def __init__(self, data: IpcActorControl):
        super().__init__(data)
        self.aggroed = bool(data.param1)


class ActorControlEffectOverTime(ActorControlBase):
    TYPE = ActorControlType.EffectOverTime

    def __init__(self, data: IpcActorControl):
        super().__init__(data)
        self.buff_id = data.param1
        self.effect_type = data.param2
        self.amount = data.param3
        self.source_actor_id = data.param4

    @property
    def known_effect_type(self) -> typing.Optional[EffectType]:
        try:
            return EffectType(self.effect_type)
        except ValueError:
            return None


class ActorControlDeath(ActorControlBase):
    TYPE = ActorControlType.Death

    def __init__(self, data: IpcActorControl):
        super().__init__(data)
        self.some_actor_id = data.param1
        self.defeated_by_actor_id = data.param2


class ActorControlCastInterrupt(ActorControlBase):
    TYPE = ActorControlType.CastInterrupt

    def __init__(self, data: IpcActorControl):
        super().__init__(data)
        self.action_id = data.param3
        self.interrupted_from_damage = data.param4 == 1


class ActorControlClassJobChange(ActorControlBase):
    TYPE = ActorControlType.ClassJobChange

    def __init__(self, data: IpcActorControl):
        super().__init__(data)
        self.class_or_job = data.param1


class ActorControlMarkTarget(ActorControlBase):
    TYPE = ActorControlType.MarkTarget

    def __init__(self, data: IpcActorControlTarget):
        super().__init__(data)
        self.source_actor_id = data.param2
        self.target_actor_id = data.target_id
        self.sign_id = TargetMarkerType(data.param1 & 0xFF)
