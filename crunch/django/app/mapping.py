import pydeck
import pandas as pd


def item_map(item):
    geo_attributes = item.descendant_latlongattributes()

    plot_data = [
        dict(
            latitude=float(attribute.latitude),
            longitude=float(attribute.longitude),
            item=str(attribute.item),
            url=str(attribute.item.get_absolute_url()),
        )
        for attribute in geo_attributes
    ]
    df = pd.DataFrame(plot_data)

    # ICON_URL = "https://upload.wikimedia.org/wikipedia/commons/9/92/Ic_location_on_48px.svg"
    # ICON_WIDTH = 48
    # ICON_HEIGHT = 48

    ICON_URL = "https://upload.wikimedia.org/wikipedia/commons/6/65/OOjs_UI_icon_mapPin-progressive.svg"
    ICON_WIDTH = 20
    ICON_HEIGHT = 20

    icon_data = {
        "url": ICON_URL,
        "width": ICON_WIDTH,
        "height": ICON_HEIGHT,
        "anchorY": ICON_HEIGHT,
    }

    df["icon_data"] = None
    for i in df.index:
        df.at[i, "icon_data"] = icon_data

    layer = pydeck.Layer(
        "IconLayer",
        df,
        pickable=True,
        get_icon="icon_data",
        get_size=20,
        get_position=["longitude", "latitude"],
    )

    view_state = pydeck.ViewState(
        latitude=df["latitude"].mean(),
        longitude=df["longitude"].mean(),
        zoom=2,
        min_zoom=1,
        max_zoom=16,
        pitch=0,
        bearing=0,
    )

    map = pydeck.Deck(layers=[layer], initial_view_state=view_state, map_style="road")

    return map
