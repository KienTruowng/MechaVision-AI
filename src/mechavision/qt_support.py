"""Trợ giúp Qt tiếng Việt và xuất dữ liệu Unicode cho giao diện desktop."""
import csv
import itertools
import numpy as np
from PySide6.QtCore import QTranslator
from PySide6.QtWidgets import QMessageBox
import pyqtgraph as pg
from pyqtgraph.GraphicsScene import exportDialog
from pyqtgraph.exporters import CSVExporter

class _VietnameseQtTranslator(QTranslator):
    """Các nhãn Qt chuẩn xuất hiện trong hộp chọn tệp và menu nhập văn bản."""
    labels={
        '&Delete':'&Xóa','&Look in:':'&Thư mục:','&New Folder':'Thư mục &mới',
        '&Open':'&Mở','&Rename':'Đổi &tên','All Files (*)':'Tất cả tệp (*)',
        'Back':'Quay lại','Forward':'Tiến tới','Go back':'Quay lại',
        'Go forward':'Tiến tới','Parent Directory':'Thư mục cha',
        'Go to the parent directory':'Về thư mục cha','Create New Folder':'Tạo thư mục mới',
        'Create a New Folder':'Tạo thư mục mới','Detail View':'Xem chi tiết',
        'List View':'Xem danh sách','Change to detail view mode':'Chuyển sang chế độ chi tiết',
        'Change to list view mode':'Chuyển sang chế độ danh sách','File &name:':'Tên &tệp:',
        'Files':'Tệp','Files of &type:':'&Loại tệp:','Show ':'Hiển thị ',
        'Show &hidden files':'Hiện tệp ẩ&n','Sidebar':'Thanh bên',
        'List of places and bookmarks':'Danh sách vị trí và dấu trang',
        'Date Modified':'Ngày sửa đổi','My Computer':'Máy tính','Computer':'Máy tính',
        'Name':'Tên','Size':'Kích thước','Type':'Loại','File':'Tệp','Folder':'Thư mục',
        'Directory':'Thư mục','%1 File':'Tệp %1','File Folder':'Thư mục tệp',
        'Cancel':'Hủy','OK':'Đóng','Open':'Mở','Close':'Đóng','Save':'Lưu',
        '&Undo':'&Hoàn tác','&Redo':'&Làm lại','Cu&t':'Cắ&t','&Copy':'&Sao chép',
        '&Paste':'&Dán','Delete':'Xóa','Select All':'Chọn tất cả','Select &All':'Chọn tất cả',
        'Undo':'Hoàn tác','Redo':'Làm lại','Cut':'Cắt','Copy':'Sao chép','Paste':'Dán',
        'New Folder':'Thư mục mới','File not found':'Không tìm thấy tệp',
        '%1\nFile not found.\nPlease verify the correct file name was given.':'%1\nKhông tìm thấy tệp.\nHãy kiểm tra lại tên tệp.',
        'Directory not found':'Không tìm thấy thư mục',
        '%1\nDirectory not found.\nPlease verify the correct directory name was given.':'%1\nKhông tìm thấy thư mục.\nHãy kiểm tra lại tên thư mục.',
        'ViewBox options':'Tùy chọn vùng xem','View All':'Xem toàn bộ','axis':'trục',
        'Mouse Mode':'Chế độ chuột','3 button':'Ba nút','1 button':'Một nút',
        'Plot Options':'Tùy chọn biểu đồ','Transforms':'Biến đổi','Downsample':'Giảm mẫu',
        'Average':'Trung bình','Alpha':'Độ trong suốt','Grid':'Lưới','Points':'Điểm',
        'Clip to View':'Giới hạn theo vùng xem','Max Traces:':'Số đường tối đa:',
        'Peak':'Đỉnh','Forget hidden traces':'Xóa đường đã ẩn khỏi bộ nhớ',
        'Mean':'Trung bình','Subsample':'Lấy mẫu thưa','Auto':'Tự động',
        'Log X':'Logarit X','Log Y':'Logarit Y','Y vs. Y\'':'Y theo đạo hàm Y',
        'Power Spectrum (FFT)':'Phổ công suất (FFT)','Subtract Mean':'Trừ trung bình',
        'Show X Grid':'Hiện lưới X','Show Y Grid':'Hiện lưới Y','Opacity':'Độ đục',
        'Link Axis:':'Liên kết trục:','Manual':'Thủ công','Invert Axis':'Đảo trục',
        'Mouse Enabled':'Cho phép chuột','Visible Data Only':'Chỉ dữ liệu nhìn thấy',
        'Auto Pan Only':'Chỉ tự động dịch chuyển','Export...':'Xuất…','Export':'Xuất',
        'Item to export:':'Đối tượng cần xuất:','Export format':'Định dạng xuất',
        'Export options':'Tùy chọn xuất','Entire Scene':'Toàn bộ vùng đồ thị',
        'Image File (PNG, TIF, JPG, ...)':'Tệp ảnh (PNG, TIF, JPG, …)',
        'Scalable Vector Graphics (SVG)':'Đồ họa vector SVG','CSV from plot data':'CSV từ dữ liệu biểu đồ',
        'Matplotlib Window':'Cửa sổ Matplotlib','HDF5 Export: plot (x,y)':'Xuất HDF5: biểu đồ (x,y)',
        'CSV of original plot data':'CSV từ dữ liệu biểu đồ gốc',
        'Scalable Vector Graphics':'Đồ họa vector SVG',
        'width':'Chiều rộng','height':'Chiều cao','antialias':'Khử răng cưa',
        'background':'Nền','invertValue':'Đảo độ sáng','scaling stroke':'Co giãn nét',
        'separator':'Dấu phân cách','precision':'Độ chính xác','columnMode':'Bố trí cột',
        'params':'Tham số','Plot':'Biểu đồ','ViewBox':'Vùng xem',
        'comma':'Dấu phẩy','tab':'Dấu tab','(x,y) per plot':'(x,y) cho từng đường',
        '(x,y,y,y) for all plots':'(x,y,y,y) cho tất cả đường',
        'Display averages of the curves displayed in this plot. The parameter list allows you to choose parameters to average over (if any are available).':'Hiển thị trung bình các đường trong biểu đồ. Chọn các tham số cần lấy trung bình nếu có.',
        'Plot only the portion of each curve that is visible. This assumes X values are uniformly spaced.':'Chỉ vẽ phần đường đang nhìn thấy; giả định các giá trị X cách đều.',
        'If multiple curves are displayed in this plot, check this box to limit the number of traces that are displayed.':'Giới hạn số đường hiển thị khi biểu đồ có nhiều đường.',
        'Downsample by drawing a saw wave that follows the min and max of the original data. This method produces the best visual representation of the data but is slower.':'Giảm mẫu theo cực tiểu và cực đại dữ liệu gốc; thể hiện rõ biến thiên nhưng chậm hơn.',
        'If multiple curves are displayed in this plot, check "Max Traces" and set this value to limit the number of traces that are displayed.':'Bật giới hạn số đường rồi đặt số đường tối đa được hiển thị.',
        'If MaxTraces is checked, remove curves from memory after they are hidden (saves memory, but traces can not be un-hidden).':'Khi giới hạn số đường, xóa đường đã ẩn khỏi bộ nhớ; không thể hiện lại đường đã xóa.',
        'Downsample by taking the mean of N samples.':'Giảm mẫu bằng trung bình của N mẫu.',
        'Downsample by taking the first of N samples. This method is fastest and least accurate.':'Giảm mẫu bằng mẫu đầu tiên trong N mẫu; nhanh nhất nhưng kém chính xác nhất.',
        'Automatically downsample data based on the visible range. This assumes X values are uniformly spaced.':'Tự động giảm mẫu theo vùng nhìn thấy; giả định các giá trị X cách đều.',
        'Downsample data before plotting. (plot every Nth sample)':'Giảm mẫu trước khi vẽ, lấy mỗi mẫu thứ N.',
        '<html><head/><body><p>Links this axis with another view. When linked, both views will display the same data range.</p></body></html>':'Liên kết trục với vùng xem khác để dùng chung khoảng dữ liệu.',
        '<html><head/><body><p>Percent of data to be visible when auto-scaling. It may be useful to decrease this value for data with spiky noise.</p></body></html>':'Tỷ lệ dữ liệu nhìn thấy khi tự co giãn; có thể giảm khi dữ liệu có nhiễu xung.',
        '<html><head/><body><p>Automatically resize this axis whenever the displayed data is changed.</p></body></html>':'Tự co giãn trục khi dữ liệu thay đổi.',
        '<html><head/><body><p>Set the range for this axis manually. This disables automatic scaling. </p></body></html>':'Đặt khoảng trục thủ công và tắt tự co giãn.',
        '<html><head/><body><p>Minimum value to display for this axis.</p></body></html>':'Giá trị nhỏ nhất của trục.',
        '<html><head/><body><p>Maximum value to display for this axis.</p></body></html>':'Giá trị lớn nhất của trục.',
        '<html><head/><body><p>Inverts the display of this axis. (+y points downward instead of upward)</p></body></html>':'Đảo chiều hiển thị trục (chiều dương y hướng xuống).',
        '<html><head/><body><p>Enables mouse interaction (panning, scaling) for this axis.</p></body></html>':'Cho phép dịch chuyển và co giãn trục bằng chuột.',
        '<html><head/><body><p>When checked, the axis will only auto-scale to data that is visible along the orthogonal axis.</p></body></html>':'Chỉ tự co giãn theo dữ liệu đang nhìn thấy trên trục vuông góc.',
        '<html><head/><body><p>When checked, the axis will automatically pan to center on the current data, but the scale along this axis will not change.</p></body></html>':'Tự dịch chuyển để căn giữa dữ liệu hiện tại và giữ nguyên tỷ lệ trục.',
    }

    def translate(self,context,sourceText,disambiguation=None,n=-1):
        return self.labels.get(sourceText,'')


class _Utf8CSVExporter(CSVExporter):
    """Xuất các đường của dashboard bằng UTF-8, tránh lỗi bảng mã Windows."""
    def export(self,fileName=None):
        if not isinstance(self.item,pg.PlotItem):
            raise ValueError('Hãy chọn một biểu đồ để xuất CSV.')
        if fileName is None:
            self.fileSaveDialog(filter=['*.csv','*.tsv'])
            return
        headers=[];columns=[]
        for item in self.item.items:
            if not hasattr(item,'implements') or not item.implements('plotData'):continue
            x,y=item.getOriginalDataset() if hasattr(item,'getOriginalDataset') else item.getData()
            if x is None:continue
            name=item.name() or f'Đường {len(headers)}'
            if self.params['columnMode']=='(x,y) per plot' or not columns:
                headers.append(name+'_x');columns.append(x)
            headers.append(name+'_y');columns.append(y)
        separator=',' if self.params['separator']=='comma' else '\t'
        with open(fileName,'w',newline='',encoding='utf-8') as stream:
            writer=csv.writer(stream,delimiter=separator)
            writer.writerow(headers)
            for row in itertools.zip_longest(*columns,fillvalue=''):
                writer.writerow([value if isinstance(value,str) else
                    np.format_float_positional(value,precision=self.params['precision']) for value in row])


class _VietnameseExportDialog(exportDialog.ExportDialog):
    """Dịch nhãn cây và tham số xuất, giữ nguyên tên/giá trị của bộ xuất dữ liệu."""
    def updateItemList(self,*args,**kwargs):
        super().updateItemList(*args,**kwargs)
        def visit(item):
            item.setText(0,_VietnameseQtTranslator.labels.get(item.text(0),item.text(0)))
            for index in range(item.childCount()):visit(item.child(index))
        for index in range(self.ui.itemTree.topLevelItemCount()):
            visit(self.ui.itemTree.topLevelItem(index))

    def exportFormatChanged(self,*args,**kwargs):
        super().exportFormatChanged(*args,**kwargs)
        if self.currentExporter is None:return
        if isinstance(self.currentExporter,CSVExporter):
            self.currentExporter=_Utf8CSVExporter(self.currentExporter.item)
        params=self.currentExporter.parameters()
        if params is None:return
        for param in [params,*params.children()]:
            param.setOpts(title=_VietnameseQtTranslator.labels.get(param.name(),param.name()))
            limits=param.opts.get('limits')
            if param.type()=='list' and isinstance(limits,list) and all(isinstance(v,str) for v in limits):
                param.setLimits({_VietnameseQtTranslator.labels.get(v,v):v for v in limits})
        self.ui.paramTree.setParameters(params)

    def show(self,*args,**kwargs):
        super().show(*args,**kwargs)
        self.resize(640,520)



def _message(parent,title,text,icon=QMessageBox.Warning):
    box=QMessageBox(icon,title,text,QMessageBox.Ok,parent)
    box.button(QMessageBox.Ok).setText('Đóng')
    box.exec()


