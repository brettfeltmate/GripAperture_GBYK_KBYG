# TODO: document

from construct import Struct
from typing import List, Dict, Union, Tuple
from DescriptionStructures import *




class descriptionUnpacker:
    def __init__(self, unparsed_bytestream: bytes = None, NatNetStreamVersion: List[int] = None) -> None:
        self.natnet_version = NatNetStreamVersion        # Determines which structure to use
        self._structure = self._get_structure()     # Asset specific Construct Struct
        self._description = None                           # To store parsed description

        # Parse data if provided during instantiation
        if unparsed_bytestream is not None:
            self.parse(unparsed_bytestream)

    # Fetches child-appropriate description Struct(), conditioned on motive version
    def _get_structure(self) -> Struct:
        try:
            return DESCRIPTION_STRUCTS[type(self)]
        except KeyError:
            raise ValueError(f"MoCapAsset._get_structure() | Unrecognized asset type.\n\tExpected: {DESCRIPTION_STRUCTS.keys()}\n\tSupplied: {type(self)}")
    
    # Returns landing position in datastream after parsing
    def relative_offset(self) -> int:
        # NOTE: Offset pruned out when dump()ing data 
        if self._description is not None:
            return self._description.relative_offset
        

        # TODO: Expected offset might be handy
        return 0
        
    # Shadows Construct.Struct.parse() method
    def parse(self, unparsed_bytestream: bytes) -> None:
        self._description = self._structure.parse(unparsed_bytestream)

    # Coerces description parcels into list[dict]; bundling procedure varies by child
    #       NOTE: Children drop terminal entries (1 = obj addr, -1 = offset)
    def data(self) -> List[Dict]:
        raise NotImplementedError("AssetDescriptionStruct.dump() | Must be implemented by child class.")
    
#
# DescriptionAsset Child classes
#
    
    
# Parses N-i MarkerSets, each composed of N-j Markers
class markerSetDescription(descriptionUnpacker):
    def __init__(self, unparsed_bytestream: bytes = None, NatNetStreamVersion: List[int] = None) -> None:
        super().__init__(unparsed_bytestream, NatNetStreamVersion)

    def data(self) -> List[Dict]:
        return [dict(list(marker.items())[1:]) 
                for marker in self._description.children]
    

# Parses N-i RigidBodies NOT integral to skeletons, each composed of N-j RigidBody(s)
class rigidBodyDescription(descriptionUnpacker):
    def __init__(self, unparsed_bytestream: bytes = None, NatNetStreamVersion: List[int] = None) -> None:
        super().__init__(unparsed_bytestream, NatNetStreamVersion)

    def data(self) -> List[Dict]:
        return [dict(list(rigidBodyMarker.items())[1:]) 
                for rigidBodyMarker in self._description.children]
    
# Parses N-i Skeletons, each composed of N-j RigidBodies, each composed of N-k RigidBody(s)
class skeletonDescription(descriptionUnpacker):
    def __init__(self, unparsed_bytestream: bytes = None, NatNetStreamVersion: List[int] = None) -> None:
        super().__init__(unparsed_bytestream, NatNetStreamVersion)

    def data(self) -> List[Dict]:
        return [dict(list(rigidBodyMarker.items())[1:]) 
                for rigidBody in self._description.children
                for rigidBodyMarker in rigidBody.children]
    

class assetDescription(descriptionUnpacker):
    def __init__(self, unparsed_bytestream: bytes = None, NatNetStreamVersion: List[int] = None) -> None:
        super().__init__(unparsed_bytestream, NatNetStreamVersion)

    def data(self, asset_type: str) -> List[Dict]:
        if (asset_type == "RigidBodies"):
            return [dict(list(rigidBodyMarker.items())[1:])
                    for rigidBody in self._description.rigid_body_children
                    for rigidBodyMarker in rigidBody.children]
        elif (asset_type == "Markers"):
            return [dict(list(marker.items())[1:])
                    for marker in self._description.marker_children]
        else:
            raise ValueError(f"assetDescription.export() | asset_type must be 'RigidBodies' or 'Markers', got: {asset_type}")
    
# Parses N-i ForcePlates, each plate composed of N-j Channel(s)
class forcePlateDescription(descriptionUnpacker):
    def __init__(self, unparsed_bytestream: bytes = None, NatNetStreamVersion: List[int] = None) -> None:
        super().__init__(unparsed_bytestream, NatNetStreamVersion)

    def data(self) -> List[Dict]:
        # TODO: Figuring out tidy way of returning matrices is Future Brett's problem
        pass
        return [dict(list(channel.items())[1:]) 
                for plate in self._description.children
                for channel in plate.children]
    

# Parses N-i Devices, each device composed of N-j Channel(s)
class deviceDescription(descriptionUnpacker):
    def __init__(self, unparsed_bytestream: bytes = None, NatNetStreamVersion: List[int] = None) -> None:
        super().__init__(unparsed_bytestream, NatNetStreamVersion)

    def data(self) -> List[Dict]:
        return [dict(list(channel.items())[1:]) 
                for device in self._description.children
                for channel in device.children]
    

class cameraDescription(descriptionUnpacker):
    def __init__(self, unparsed_bytestream: bytes = None, NatNetStreamVersion: List[int] = None) -> None:
        super().__init__(unparsed_bytestream, NatNetStreamVersion)

    def data(self) -> List[Dict]:
        return [dict(list(camera.items())[1:]) 
                for camera in self._description.children]
    

    #
# Structures dictionary for MoCap asset descriptions
# NOTE: Original idea was to support backwards compatibility, but that's Future Brett's problem

DESCRIPTION_STRUCTS = {
    markerSetDescription:  descStruct_MarkerSet,
    rigidBodyDescription:  descStruct_RigidBody,
    skeletonDescription:   descStruct_Skeleton,
    assetDescription:      descStruct_Asset,
    forcePlateDescription: descStruct_ForcePlate,
    deviceDescription:     descStruct_Device,
    cameraDescription:     descStruct_Camera
}
    
    # Aggregate frame data
class Descriptions:
    def __init__(self) -> None:
        
        # Aggregate Frame Data
        self._descriptions = {
            'MarkerSets': None, 
            'RigidBodies': None, 
            # 'Skeleton': None,
            # 'AssetRigidBody': None,
            # 'AssetMarker': None,
            # 'ForcePlate': None, 
            # 'Device': None, 
            # 'Camera': None
        }
    
    # Log frame data for a given asset type
    def log(self, asset_type: str, asset_description: List[Dict]) -> None:
        self._descriptions[asset_type] = asset_description

    # Export frame data for desired asset types; also allows for omission
    def __validate_export_arg(self, arg: Union[Tuple[str,...], str], name: str) -> Tuple[str, ...]:
        if isinstance(arg, str):
            return (arg,)
        elif isinstance(arg, tuple) and all(isinstance(i, str) for i in arg):
            return arg
        else:
            raise TypeError(f"Descriptions.export() | {name} must be str or tuple thereof")

    # Export descriptions for desired asset types; also allows for omission
    def export(self, include: Union[Tuple[str, ...], str], exclude: Union[Tuple[str, ...], str] = None) -> Dict[str, List[Dict]]:
        # include = self.__validate_export_arg(include, "include")

        # if exclude is not None:
        #     exclude = self.__validate_export_arg(exclude, "exclude")
        #     return {k: v for k, v in self._framedata.items() 
        #             if k in include and k not in exclude}
            
        # return {k: v for k, v in self._framedata.items() if k in include}

        return self._descriptions


    