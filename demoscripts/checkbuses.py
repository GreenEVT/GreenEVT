# Based on https://gist.github.com/dwyerk/10561690

import sqlite3
import shapely.wkb
from shapely import geometry
import matplotlib.pyplot as plt
from descartes import PolygonPatch
from shapely.ops import cascaded_union, polygonize
from scipy.spatial import Delaunay
import numpy as np
import math


def plot_polygon(polygon):
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111)
    margin = 0.3

    x_min, y_min, x_max, y_max = polygon.bounds

    ax.set_xlim([x_min - margin, x_max + margin])
    ax.set_ylim([y_min - margin, y_max + margin])
    patch = PolygonPatch(polygon, fc="#999999", ec="#000000", fill=True, zorder=-1)
    ax.add_patch(patch)
    return fig


def alpha_shape(points, alpha):
    """
    Compute the alpha shape (concave hull) of a set
    of points.
    @param points: Iterable container of points.
    @param alpha: alpha value to influence the
        gooeyness of the border. Smaller numbers
        don't fall inward as much as larger numbers.
        Too large, and you lose everything!
    """
    if len(points) < 4:
        # When you have a triangle, there is no sense
        # in computing an alpha shape.
        return geometry.MultiPoint(list(points)).convex_hull

    coords = np.array([point.coords[0] for point in points])
    tri = Delaunay(coords)
    triangles = coords[tri.vertices]
    a = (
        (triangles[:, 0, 0] - triangles[:, 1, 0]) ** 2
        + (triangles[:, 0, 1] - triangles[:, 1, 1]) ** 2
    ) ** 0.5
    b = (
        (triangles[:, 1, 0] - triangles[:, 2, 0]) ** 2
        + (triangles[:, 1, 1] - triangles[:, 2, 1]) ** 2
    ) ** 0.5
    c = (
        (triangles[:, 2, 0] - triangles[:, 0, 0]) ** 2
        + (triangles[:, 2, 1] - triangles[:, 0, 1]) ** 2
    ) ** 0.5
    s = (a + b + c) / 2.0
    areas = (s * (s - a) * (s - b) * (s - c)) ** 0.5
    circums = a * b * c / (4.0 * areas)
    filtered = triangles[circums < (1.0 / alpha)]
    edge1 = filtered[:, (0, 1)]
    edge2 = filtered[:, (1, 2)]
    edge3 = filtered[:, (2, 0)]
    edge_points = np.unique(np.concatenate((edge1, edge2, edge3)), axis=0).tolist()
    m = geometry.MultiLineString(edge_points)
    triangles = list(polygonize(m))
    return cascaded_union(triangles), edge_points


conn = sqlite3.connect("../data/UDS.db")
c = conn.cursor()


buses = []
for row in c.execute("SELECT long, lat FROM buses WHERE active_load > 0 "):
    buses.append(geometry.Point([row[0], row[1]]))

xbus = [p.coords.xy[0] for p in buses]
ybys = [p.coords.xy[1] for p in buses]

concave_hull, edge_points = alpha_shape(buses, alpha=1000)
_ = plot_polygon(concave_hull)


count = 0
parcelsmissing = []
updates = []
for parcel in c.execute("SELECT ogc_fid, GEOMETRY from parcels WHERE bus_id = -1"):
    p = shapely.wkb.loads(parcel[1])
    if p.within(concave_hull):
        parcelsmissing.append(p)
        updates.append((-2, parcel[0]))
        count = count + 1

xp = [p.coords.xy[0] for p in parcelsmissing]
yp = [p.coords.xy[1] for p in parcelsmissing]

_ = plt.plot(xp, yp, "o", color="#f16824")

print(len(updates))

# Update the buses within the area
# c.executemany('UPDATE parcels SET bus_id=? WHERE ogc_fid=?',updates)
# conn.commit()


print("Parcel missing a bus within the concave hull: " + str(count))

plt.show()
conn.close()
