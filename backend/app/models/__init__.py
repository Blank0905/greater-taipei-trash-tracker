from .user import User, Favorite, Notification
from .station import Area, BagRegulation, Route, Station
from .schedule import StationSchedule

# 這樣做可以在外面直接從 app.models import User, Station... 而不用管是在哪個小檔案裡
