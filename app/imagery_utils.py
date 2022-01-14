import os
import subprocess
import ee
from geemap import png_to_gif
import matplotlib.pyplot as plt
from geemap.cartoee import get_map, add_gridlines, add_scale_bar_lite, add_north_arrow

def new_get_image_collection_gif(
  ee_ic,
  out_dir,
  out_gif,
  vis_params,
  region,
  cmap=None,
  proj=None,
  fps=10,
  mp4=False,
  grid_interval=None,
  plot_title="",
  date_format="YYYY-MM-dd",
  fig_size=(10, 10),
  dpi_plot=100,
  file_format="png",
  north_arrow_dict={},
  scale_bar_dict={},
  verbose=True,
  max_frames=10
):
    """Download all the images in an image collection and use them to generate a gif/video.
    Args:
        ee_ic (object): ee.ImageCollection
        out_dir (str): The output directory of images and video.
        out_gif (str): The name of the gif file.
        vis_params (dict): Visualization parameters as a dictionary.
        region (list | tuple): Geospatial region of the image to render in format [E,S,W,N].
        fps (int, optional): Video frames per second. Defaults to 10.
        mp4 (bool, optional): Whether to create mp4 video.
        grid_interval (float | tuple[float]): Float specifying an interval at which to create gridlines, units are decimal degrees. lists will be interpreted a (x_interval, y_interval), such as (0.1, 0.1). Defaults to None.
        plot_title (str): Plot title. Defaults to "".
        date_format (str, optional): A pattern, as described at http://joda-time.sourceforge.net/apidocs/org/joda/time/format/DateTimeFormat.html. Defaults to "YYYY-MM-dd".
        fig_size (tuple, optional): Size of the figure.
        dpi_plot (int, optional): The resolution in dots per inch of the plot.
        file_format (str, optional): Either 'png' or 'jpg'.
        north_arrow_dict (dict, optional): Parameters for the north arrow. See https://geemap.org/cartoee/#geemap.cartoee.add_north_arrow. Defaults to {}.
        scale_bar_dict (dict, optional): Parameters for the scale bar. See https://geemap.org/cartoee/#geemap.cartoee.add_scale_bar. Defaults. to {}.
        verbose (bool, optional): Whether or not to print text when the program is running. Defaults to True.
    """
    out_dir = os.path.abspath(out_dir)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    out_gif = os.path.join(out_dir, out_gif)

    count = int(ee_ic.size().getInfo())
    names = ee_ic.aggregate_array("system:index").getInfo()
    images = ee_ic.toList(count)

    dates = ee_ic.aggregate_array("system:time_start")
    dates = dates.map(lambda d: ee.Date(d).format(date_format)).getInfo()

    # avoid too many frames
    if count > max_frames:
        return (True, f'The time span is too long. We would need to process {count} single frames. Please choose a shorter period!')

    # list of file name
    img_list = []

    for i, date in enumerate(dates):
        image = ee.Image(images.get(i))
        name = str(names[i])
        #name = name + "." + file_format
        name = str(i).zfill(3) + "_" + name + "." + file_format
        out_img = os.path.join(out_dir, name)
        img_list.append(out_img)

        if verbose:
            print(f"Downloading {i+1}/{count}: {name} ...")

        # Size plot
        plt.figure(figsize=fig_size)

        # Plot image
        ax = get_map(image, region=region, vis_params=vis_params, cmap=cmap, proj=proj)

        # Add grid
        if grid_interval is not None:
            add_gridlines(ax, interval=grid_interval, linestyle=":")

        # Add title
        if len(plot_title) > 0:
            ax.set_title(label=plot_title + " " + date + "\n", fontsize=15)

        # Add scale bar
        if len(scale_bar_dict) > 0:
            add_scale_bar_lite(ax, **scale_bar_dict)
        # Add north arrow
        if len(north_arrow_dict) > 0:
            add_north_arrow(ax, **north_arrow_dict)

        # Save plot
        plt.savefig(fname=out_img, dpi=dpi_plot)

        plt.clf()
        plt.close()

    out_gif = os.path.abspath(out_gif)
    png_to_gif(out_dir, out_gif, fps)
    if verbose:
        print(f"GIF saved to {out_gif}")

    if mp4:

        video_filename = out_gif.replace(".gif", ".mp4")

        try:
            import cv2
        except ImportError:
            print("Installing opencv-python ...")
            subprocess.check_call(["python", "-m", "pip", "install", "opencv-python"])
            import cv2

        # Video file name
        output_video_file_name = os.path.join(out_dir, video_filename)

        frame = cv2.imread(img_list[0])
        height, width, _ = frame.shape
        frame_size = (width, height)
        fps_video = fps

        # Make mp4
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")

        # Function
        def convert_frames_to_video(
            input_list, output_video_file_name, fps_video, frame_size
        ):

            """Convert frames to video
            Args:
                input_list (list): Downloaded Image Name List.
                output_video_file_name (str): The name of the video file in the image directory.
                fps_video (int): Video frames per second.
                frame_size (tuple): Frame size.
            """
            out = cv2.VideoWriter(output_video_file_name, fourcc, fps_video, frame_size)
            num_frames = len(input_list)

            for i in range(num_frames):
                img_path = input_list[i]
                img = cv2.imread(img_path)
                out.write(img)

            out.release()
            cv2.destroyAllWindows()

        # Use function
        convert_frames_to_video(
            input_list=img_list,
            output_video_file_name=output_video_file_name,
            fps_video=fps_video,
            frame_size=frame_size,
        )

        if verbose:
            print(f"MP4 saved to {output_video_file_name}")

    # return success
    return (False, None)