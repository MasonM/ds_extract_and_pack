; Script to run the "Make seamless" plugin on every JPG, making them tileable
(let* ((filelist (cadr (file-glob "*.jpg" 1))))
	(while (not (null? filelist))
	     (let* ((filename (car filelist))
		    (image (car (gimp-file-load RUN-NONINTERACTIVE
						filename filename)))
		    (drawable (car (gimp-image-get-active-layer image))))
	       (plug-in-make-seamless RUN-NONINTERACTIVE image drawable)
	       (gimp-file-save RUN-NONINTERACTIVE
			       image drawable filename filename)
	       (gimp-image-delete image))
	     (set! filelist (cdr filelist))))
(gimp-quit 0)
