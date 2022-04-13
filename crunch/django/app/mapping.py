import pydeck
import pandas as pd
from django.db import models

from .models import LatLongAttribute

def item_map(item):
    geo_attributes = item.descendant_attributes(attribute_type=LatLongAttribute, include_self=True)

    plot_data = [
        dict(
            latitude=float(attribute.latitude),
            longitude=float(attribute.longitude),
        )
        for attribute in geo_attributes    
    ]        
    df = pd.DataFrame(plot_data)

    icon_data = {
        "url": "https://cdn.jsdelivr.net/npm/leaflet@1.6.0/dist/images/marker-icon.png",
        "width": 12,
        "height": 20,
        "anchorY": 20,
    }
    df["icon_data"] = None
    for i in df.index:
        df["icon_data"][i] = icon_data

    layer = pydeck.Layer(
        "IconLayer",
        df,
        pickable=True,
        get_icon="icon_data",
        get_size=4,
        size_scale=4,
        get_position=['longitude', 'latitude'],
    )

    view_state = pydeck.ViewState(
        latitude=df['latitude'].mean(),
        longitude=df['longitude'].mean(),
        zoom=2,
        min_zoom=1,
        max_zoom=16,
        pitch=0,
        bearing=0,
    )

    map = pydeck.Deck(layers=[layer], initial_view_state=view_state, map_style="road")

    return map
