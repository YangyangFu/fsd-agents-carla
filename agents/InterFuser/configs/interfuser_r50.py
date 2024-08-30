from mmengine import read_base

with read_base():
    from fsd.configs._base_.default_runtime import *

work_dir = '.'

# custom imports to trigger registration
custom_imports = dict(
    imports=['mmpretrain.models'],
    allow_failed_imports=False
)

point_cloud_range = [-51.2, -51.2, -5.0, 51.2, 51.2, 3.0]
img_norm_cfg = dict(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225], to_rgb=True)
class_names = [
'car','van','truck','bicycle','traffic_sign','traffic_cone','traffic_light','pedestrian','others'
]


input_modality = dict(
    use_lidar=True, 
    use_camera=True, 
    use_radar=False, 
    use_map=False, 
    use_external=True
)

camera_sensors = [
    'CAM_FRONT', 
    'CAM_FRONT_LEFT', 
    'CAM_FRONT_RIGHT', 
    'CAM_FRONT', # load one more times
]
lidar_sensors = ['LIDAR_TOP']

EMBED_DIMS = 256
PLANNING_STEPS = 10

model = dict(
    type='InterFuser',
    num_queries=411,
    embed_dims=EMBED_DIMS,
    img_backbone=dict(
        type='mmpretrain.TIMMBackbone', #timm model wrapper
        model_name='resnet50d',
        features_only=True,
        pretrained=True,
        out_indices=[4]
    ),
    pts_backbone=dict(
        type='mmpretrain.TIMMBackbone', #timm model wrapper
        model_name='resnet18d',
        features_only=True,
        pretrained=True,
        out_indices=[4]
    ),
    img_neck=dict(
        type='Conv1d',
        in_channels=2048,
        out_channels=EMBED_DIMS
    ),
    pts_neck=dict(
        type='Conv1d',
        in_channels=512,
        out_channels=EMBED_DIMS
    ),
    encoder = dict( # DetrTransformerEncoder
        type='DETRLayerSequence',
        num_layers=6,
        layer_cfgs=dict(
            type='DETRLayer',
            attn_cfgs=dict( # MultiheadAttention
                type='MultiheadAttention',
                embed_dims=EMBED_DIMS,
                num_heads=8,
                attn_drop=0.,
                proj_drop=0.
            ),
            ffn_cfgs=dict(
                type='FFN',
                embed_dims=EMBED_DIMS,
                feedforward_channels=2048,
                num_fcs=2,
                ffn_drop=0.1,
                act_cfg=dict(type='ReLU', inplace=True)
            ),
            operation_order=['self_attn', 'norm', 'ffn', 'norm'],
            batch_first=False,
        )
    ),       
    decoder = dict(  # DetrTransformerDecoder
        type='DETRLayerSequence',
        num_layers=6,
        layer_cfgs=dict(
            type='DETRLayer',
            attn_cfgs=dict( # MultiheadAttention
                type='MultiheadAttention',
                embed_dims=EMBED_DIMS,
                num_heads=8,
                attn_drop=0.,
                proj_drop=0.,
            ),
            ffn_cfgs=dict(
                type='FFN',
                embed_dims=EMBED_DIMS,
                feedforward_channels=2048,
                num_fcs=2,
                ffn_drop=0.1,
                act_cfg=dict(type='ReLU', inplace=True)
            ),
            operation_order=['self_attn', 'norm', 'cross_attn', 'norm', 'ffn', 'norm'],
            batch_first=False,
        )
    ),
    heads=dict(
        type='interfuser_heads',
        num_waypoints_queries=PLANNING_STEPS,
        num_traffic_rule_queries=1,
        num_object_density_queries=400,
        waypoints_head=dict(
            type='interfuser_gru_waypoint',
            num_waypoints=10,
            input_size=EMBED_DIMS,
            hidden_size=64,
            num_layers=1,
            dropout=0.,
            batch_first=True,
            loss_cfg=dict(
                type='MaskedSmoothL1Loss',
                beta=1.0,
                reduction='mean',
                loss_weight=1.0
            ),
            waypoints_weights=[
                0.1407441030399059,
                0.13352157985305926,
                0.12588535273178575,
                0.11775496498388233,
                0.10901991343009122,
                0.09952110967153563,
                0.08901438656870617,
                0.07708872007078788,
                0.06294267636589287,
                0.04450719328435308,
            ]),
        object_density_head=dict(
            type='interfuser_object_density',
            input_size=EMBED_DIMS + 32,
            hidden_size=64,
            output_size=7,
            loss_cfg=dict(
                type='L1Loss',
                _scope_='mmdet',
                reduction='mean',
                loss_weight=1.0
            )
        ),
        junction_head=dict(
            type='interfuser_traffic_rule',
            input_size=EMBED_DIMS,
            output_size=2,
            loss_cfg=dict(
                type='CrossEntropyLoss',
                _scope_='mmdet',
                use_sigmoid=True, # binary classification
                reduction='mean',
                loss_weight=1.0
            )
        ),
        stop_sign_head=dict(
            type='interfuser_traffic_rule',
            input_size=EMBED_DIMS,
            output_size=2,
            loss_cfg=dict(
                type='CrossEntropyLoss',
                _scope_='mmdet',
                use_sigmoid=True, # binary classification
                reduction='mean',
                loss_weight=1.0
            )
        ),
        traffic_light_head=dict(
            type='interfuser_traffic_rule',
            input_size=EMBED_DIMS,
            output_size=2,
            loss_cfg=dict(
                type='CrossEntropyLoss',
                _scope_='mmdet',
                use_sigmoid=True, # binary classification
                reduction='mean',
                loss_weight=1.0
            )
        )
    ),        
    positional_encoding=dict(
        num_feats=EMBED_DIMS//2,
        normalize=True
    ), 
    multi_view_encoding=dict(
        num_embeddings=5,
        embedding_dim=EMBED_DIMS
    ),
    data_preprocessor=dict(
        type="InterFuserDataPreprocessor")
)

controller = dict(
    # Controller
    turn_KP = 1.25,
    turn_KI = 0.75,
    turn_KD = 0.3,
    turn_n = 40,  # buffer size

    speed_KP = 5.0,
    speed_KI = 0.5,
    speed_KD = 1.0,
    speed_n = 40,  # buffer size

    max_throttle = 0.75,  # upper limit on throttle signal value in dataset
    brake_speed = 0.1,  # desired speed below which brake is triggered
    brake_ratio = 1.1,  # ratio of speed to desired speed at which brake is triggered
    clip_delta = 0.35, # maximum change in speed input to logitudinal controller

    max_speed = 5,
    collision_buffer = [2.5, 1.2],
    detect_threshold = 0.04
)

checkpoints = "agents/InterFuser/configs/interfuser.pth.tar"
save_output=True
output_dir='.outputs'
