import pyqtgraph as pg
import numpy as np

class MyGraph:
    def __init__(self, plot_widget):
        self.plot = plot_widget  

    def plot_bar_chart(self, data, labels):
        color = (52, 152, 219)  # Blue
        x_positions = np.arange(len(data))
        
        for x, height in zip(x_positions, data):
            bar = pg.BarGraphItem(
                x=[x], height=[height], width=0.8, brush=pg.mkBrush(color)
            )
            self.plot.addItem(bar)
            
            if height > 0:
                text_item = pg.TextItem(f"{int(height)}", color='black', anchor=(0.5, 0))
                text_item.setPos(x, height + 0.3)
                self.plot.addItem(text_item)
        
        self.plot.setBackground("#ddf3f6") 
        self.plot.showGrid(x=False, y=False, alpha=0)
        self.plot.setXRange(-0.5, len(data) - 0.5)
        self.plot.setYRange(0, max(data) + 10)  # Extra space for text
        self.plot.getAxis("bottom").setTicks([list(zip(x_positions, labels))])