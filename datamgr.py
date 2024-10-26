import json
import os
import re
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"]="1"
from pygame.math import Vector2 as Vec2
from math import pi, sin as _sin, cos as _cos, floor, cbrt

def deg2rad(deg):
    return deg * pi / 180

# def rad2deg(rad):
#     return rad * 180 / pi

def sin(deg):
    deg %= 360
    '''if deg == 0 or deg == 180:
        return 0.0
    if deg == 90:
        return 1.0
    if deg == 270:
        return -1.0'''
    return _sin(deg2rad(deg))

def cos(deg):
    deg %= 360
    '''if deg == 90 or deg == 270:
        return 0.0
    if deg == 0:
        return 1.0
    if deg == 180:
        return -1.0'''
    return _cos(deg2rad(deg))


def move_step(direction):  # 向 direction° 方向移动一个单位
    return Vec2(cos(direction), sin(direction))

class ApofaiDtmgr:
    def __init__(self,path=None):
        self.path=path
        if path and not self.process_data():
            print("读取失败")
            self.success=False
            return
        self.success=True
        pass
    
    class Tile:
        def __init__(self,angle=0.0):
            self.angle=angle
            self.bpm=None
            self.stdbpm=None
            self.bpmangle=0
            self.twirl=False
            self.pause=0
            self.trackColor=None
            self.secondaryTrackColor=None
            self.midspin=False
            self.hold=False
            self.pos=Vec2(0,0)
        
        def update(self,prevtile):
            if prevtile!=None:
                if self.angle==999:
                    self.midspin=True
                    self.angle=(prevtile.angle-180)
                deltaangle=(180-self.angle+prevtile.angle)%360
                self.clock_wise=prevtile.clock_wise^self.twirl
                angleoffset=(360 if deltaangle==0 and not self.midspin else deltaangle) if self.clock_wise else ((360-deltaangle) if not self.midspin else 0)
                if self.stdbpm==None:
                    self.stdbpm=prevtile.stdbpm
                elif self.stdbpm<0:
                    self.stdbpm*=-prevtile.stdbpm
                self.bpm=(self.stdbpm*(angleoffset-self.bpmangle)+prevtile.stdbpm*self.bpmangle)/angleoffset if self.bpmangle>0 and angleoffset>0 else self.stdbpm
                if self.trackColor==None:
                    self.trackColor=prevtile.trackColor
                if self.secondaryTrackColor==None:
                    self.secondaryTrackColor=prevtile.secondaryTrackColor
                self.pos+=prevtile.pos+move_step(self.angle)
                deltabeat=angleoffset/180+self.pause
                self.offset=prevtile.offset+deltabeat*60/self.bpm
                self.beat=prevtile.beat+deltabeat
                print(self.bpm,self.pause,self.angle,self.twirl,self.midspin,self.hold,deltaangle,deltabeat,self.offset,self.beat)
                
            else:
                if self.stdbpm==None:
                    self.stdbpm=100
                if self.bpm==None:
                    self.bpm=self.stdbpm
                if self.trackColor==None:
                    self.trackColor="#debb7b"
                if self.secondaryTrackColor==None:
                    self.secondaryTrackColor="#ffffff"
                self.clock_wise=1^self.twirl
                self.pos=Vec2(0,0)
                self.offset=0
                self.beat=0
                
        
    def process_data(self) -> bool:
        try:
            with open(
                    self.path, "r", encoding="utf-8-sig"
            ) as f:
                string = f.read()
                string = re.sub(",(?=\\s*?[}\\]])", "", string)  # 删除尾随逗号
                self.level = json.loads(string, strict=False)
        except UnicodeDecodeError:
            print("错误", "该谱面似乎没有使用utf-8-sig编码，所以不能解析。")
            return False
        self.title = self.level["settings"]["artist"] + (
            " - " if self.level["settings"]["artist"] and self.level["settings"]["song"] else "") + \
                     self.level["settings"]["song"]
        self.offset = self.level["settings"]["offset"]/1000
        self.countdownticks=self.level["settings"]["countdownTicks"]
        self.inibpm=self.level["settings"]["bpm"]
        self.bg_color = "#" + self.level["settings"]["backgroundColor"]
        
        self.tiles = [self.Tile()]
        self.tiles[0].trackColor=self.level["settings"]["trackColor"] if "trackColor" in self.level["settings"].keys() else "#debb7b"
        self.tiles[0].secondaryTrackColor=self.level["settings"]["secondaryTrackColor"] if "secondaryTrackColor" in self.level["settings"].keys() else "#ffffff"

        path_data_dict = {'R': 0, 'p': 15, 'J': 30, 'E': 45, 'T': 60, 'o': 75, 'U': 90, 'q': 105, 'G': 120, 'Q': 135,
                          'H': 150, 'W': 165, 'L': 180, 'x': 195, 'N': 210, 'Z': 225, 'F': 240, 'V': 255, 'D': 270,
                          'Y': 285, 'B': 300, 'C': 315, 'M': 330, 'A': 345, '5': 555, '6': 666, '7': 777, '8': 888,
                          '!': 999}

        if "angleData" in self.level:
            angledata = self.level["angleData"]
        elif "pathData" in self.level:
            angledata = [path_data_dict[i] for i in self.level["pathData"]]
        else:
            print("错误", "该谱面没有 angleData 或者 pathData，所以不能解析。")
            self.level = None
            self.title = ""
            self.offset = 0
            self.text_title = None
            self.tiles.clear()
            return False
        
        for index in range(len(self.level["angleData"] if "angleData" in self.level else self.level["pathData"])):

            self.tiles.append(self.Tile(angledata[index]))

        self.tiles[0].stdbpm = self.inibpm# * self.pitch / 100

        for action in self.level["actions"]:
            try:
                tile = self.tiles[action["floor"]+1]
                match action["eventType"]:
                    case "SetSpeed":
                        if action["speedType"] == "Bpm":
                            tile.stdbpm = action["beatsPerMinute"]# * self.pitch / 100
                            tile.bpmangle = action["angleOffset"]
                        elif action["speedType"] == "Multiplier":
                            tile.stdbpm = -action["bpmMultiplier"]
                            tile.bpmangle = action["angleOffset"]
                    case "Twirl":
                        tile.twirl = True
                    case "Pause":
                        tile.pause = action["duration"]
                    #case "RecolorTrack":
                    #    if action["startTile"][1] == "Start":
                    #        a = action["startTile"][0]
                    #    else:
                    #        a = action["startTile"][0] + action["floor"]
                    #    if action["endTile"][1] == "Start":
                    #        b = action["endTile"][0]
                    #    else:
                    #        b = action["endTile"][0] + action["floor"]
                    #    for i in range(a, b + 1):
                    #        self.tiles[i]["color"] = "#" + action["trackColor"]
                    #        self.tiles[i]["border_color"] = (
                    #                "#" + action["secondaryTrackColor"]
                    #        )
                    case "ColorTrack":
                        tile.trackColor=action["trackColor"]
                        tile.secondaryTrackColor=action["secondaryTrackColor"]
                    case "PositionTrack":
                        tile.pos=Vec2(*action["positionOffset"])
                    case "Hold":
                        tile.hold=True
                        tile.pause+=action["duration"]*2
                        #tile.pos=move_step(tile.angle)*action["distanceMultiplier"]/100*(1+action["duration"]*2)
            except IndexError:
                pass

        

        for i in range(len(self.tiles)):
            self.tiles[i].update(self.tiles[i-1] if i>0 else None)

        return True
