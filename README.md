筛选了一些造的数据和爬的数据以及主要的爬虫放到了`./lc_crawler`和`./demo_data`文件夹下。如我们在正文中介绍了，我们基于已有数据集构造数据的方式有三种，在数学上分别对应`demo_data/math`下的两个文件和一个文件夹。同时在已有数据之外，我们还爬了AoPS和leetcode的数据。AoPS的爬虫很简单原来就有人爬过形成了numina数据集，但是没有人爬过leetcode的多解，因此后者是重新写的。

众所周知现在大模型的训练主要依赖于数据和已有框架，我们的造数据主要就是筛选最具多样性的set(`./filter`)然后把这个数据弄成训练框架要求的格式(`train/generate_data.py`)。我们使用的Llama-factory，我在`train/math_divgpt.yaml`放了一个我们主实验使用的训练参数。

评测指标我们主要基于Qwen-2.5-{Math/Coder}的评价体系。其中Qwen对Math对评价不完善，因此我在他们的评测方法的基础上另外使用了`symeval`包。我将其放在了`utils/math_metric.py`。

