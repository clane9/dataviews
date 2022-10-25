# dataviews

Symbolic links + logic + multiple targets implemented in python with [`dill`](https://github.com/uqfoundation/dill).

Data views are designed to be lightweight proxies for bigger pieces of data that are easy to compute but expensive to store. In addition, they can be used to encapsulate the read/write logic for custom file formats.

## Examples

A view for reading and writing a TSV file.

```python
from functools import partial
from dataviews import View
from pandas import pd

view = View(
  "data.csv",
  partial(pd.read_csv, sep="\t"),
  partial(pd.DataFrame.to_csv, sep="\t", index=False),
)

view.save("data.csv.view")
view = View.from_path("data.csv.view")

table = view()
```
