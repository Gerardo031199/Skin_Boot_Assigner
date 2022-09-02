class Vertex:
    
  def __init__(self, x, y, z):
    self.x = x
    self.y = y
    self.z = z

  def __iter__(self):
    return iter([self.x, self.y, self.z])

class VertexNormal:

  def __init__(self, x, y, z):
    self.x = x
    self.y = y
    self.z = z

  def __iter__(self):
    return iter([self.x, self.y, self.z])

class VertexTexture:

  def __init__(self, u, v):
    self.u = u
    self.v = v

  def __iter__(self):
    return iter([self.u, self.v])

class PolygonalFace:

    def __init__(self, i1, i2, i3):
        self.i1 = i1
        self.i2 = i2
        self.i3 = i3

    def __iter__(self):
        return iter([self.i1, self.i2, self.i3])
