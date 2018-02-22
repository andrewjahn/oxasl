#!/bin/bash

# OXFORD_ASL: Converts ASL images in to perfusion maps
#
# Michael Chappell, FMRIB Image Analysis Group & IBME
#
# Copyright (c) 2008-2016 University of Oxford
#
# SHCOPYRIGHT

# Make script use local copies of helper scripts/programs in the same
# directory, if present. This allows for multiple versions of the scripts
# to be used, possibly with bundled dependencies
PATH=`dirname $0`:${FSLDEVDIR}/bin:${FSLDIR}/bin:${PATH}

def add_oxasl_options(parser, ignore=[]):
    g = AslOptionGroup(parser, "Main Options", ignore=ignore)
    g.add_option("-m", dest="mask", help="Brain mask (in native space of ASL data)")
    g.add_option("--spatial", dest="spatial", help="Use adaptive spatial smoothing on perfusion", action="store_true", default=False)
    g.add_option("--wp", dest="wp", help="Analysis which conforms to the 'white papers' (Alsop et al 2014)", action="store_true", default=False)
    g.add_option("--mc", dest="mc", help="Motion correct data", action="store_true", default=False)
    g.add_option("--mode", dest="more", help="Show extended options", action="store_true", default=False)
    parser.add_option_group(g)
    g = AslOptionGroup(parser, "Acquisition/Data specific", ignore=ignore)
    g.add_option("--iaf", dest="iaf", help="input ASl format: diff,tc,ct", default="diff")
    g.add_option("--ibf", dest="ibf", help="input block format (for multi-TI): rpt,tis", default="rpt")
    g.add_option("--artsupp", dest="artsupp", help="Arterial suppression (vascular crushing) was used", action="store_true", default=False)
    g.add_option("--bolus", dest="bolus", help="Bolus duration", type=float, default=1.0)
    g.add_option("--bat", dest="bat", help="Bolus arrival time (default=0.7 (pASL), 1.3 (cASL)", type=float)
    g.add_option("--t1", dest="t1", help="Tissue T1 value", type=float, default=1.3)
    g.add_option("--t1b", dest="t1b", help="Blood T1 value", type=float, default=1.65)
    g.add_option("--slicedt", dest="slicedt", help="Timing difference between slices", type=float, default=0.0)
    g.add_option("--sliceband", dest="sliceband", help="Number of slices per pand in multi-band setup", type=int)
    g.add_option("--casl", dest="casl", help="ASL acquisition is  pseudo cASL (pcASL) rather than pASL", action="store_true", default=False)
    g.add_option("", dest="", help="", action="store_true", default=False)
    g.add_option("", dest="", help="", action="store_true", default=False)
    g.add_option("", dest="", help="", action="store_true", default=False)
    g.add_option("", dest="", help="", action="store_true", default=False)
    g.add_option("", dest="", help="", action="store_true", default=False)
    g.add_option("", dest="", help="", action="store_true", default=False)
    parser.add_option_group(g)
    g = AslOptionGroup(parser, "Structural image (optional) (see also Registration)", ignore=ignore)
    g.add_option("--fslanat", dest="fslanat", help=" An fsl_anat directory from structural image")
    g.add_option("-s", dest="struct", help="Structural image (whole head)")
    g.add_option("--sbrain", dest="sbrain", help="Structural image (Brain extracted)")
    g.add_option("--fastsrc", dest="fastsrc", help="Images from a FAST segmentation - if not set FAST will be run on structural image")
    g.add_option("--senscorr", dest="senscorr", help="Use bias field (from segmentation) for sensitivity correction", action="store_true", default=False)
    g.add_option("", dest="", help="")
    g.add_option("", dest="", help="")
    g.add_option("", dest="", help="")
    parser.add_option_group(g)
    g = AslOptionGroup(parser, "Calibration", ignore=ignore)  
    echo " --M0        : (single) precomputed M0 value (e.g. from having run a separate calibration)"
    echo " --alpha     : Inversion efficiency - {default: 0.98 (pASL); 0.85 (cASL)}"
    echo "  To supply calibration data:"
    echo "  -c          : M0 calibration image (proton density or mean control image)"
    echo "  --tr        : TR of calibration data - {default: 3.2 s}"
    echo "  --cmethod   : Calibration method: "
    echo "                single - default if structural image is supplied"
    echo "                 M0 value will be calculated within automatically created CSF mask"
    echo "                voxel  - default if no structral image is supplied"
    echo "                 voxelwise M0 values derrived from calibration image"
    echo ""
}

Usage_extended() {
    echo "Extended options (all optional):"
    echo " Analysis"
    echo " --artoff     : Do not infer arterial signal - (same as --artsupp)"
    echo " --fixbolus   : Bolus duration is fixed, e.g. by QUIPSSII or CASL (otheriwse it will be estimated)"
    echo "                 {default: on (cASL); off (pASL)"
    echo " --fixbat     : Fix the bolus arrival time (to value specified by --bat)"
    echo " --infert1    : Incorporate uncertainty in T1 values in analysis"
    echo " --fulldata   : Never average multiple measurements at each TI"
    echo " --noiseprior : Use an informative prior for the noise estimation"
    echo "   --noisesd  : Set a custom noise std. dev. for the nosie prior"

    echo " Registration (requires structural image)"
    echo " --asl2struc : transformation matrix from asl data to structural image"
    echo "                (skips registration)"
    echo " --regfrom   : image to use a basis for inital registration (already BETed)"
    echo "               (must be same resolution as ASL data)"
#    echo " -t          : structural to standard space transformation matrix"
#    echo "               (requires structural image)"
#    echo " --structout : (also) save the maps in structural space (for use with -t)"
#    echo " -S          : standard brain image - {default: MNI152_T1_2mm}"
    echo " -r          : low resolution structural image (already BETed)"

    echo " Calibration"
    echo "  --cgain     : Relative gain between calibration and ASL image - {default: 1}"
    echo "   extended options for voxel"
    echo "    --t1t      : Assumed T1 of tissue (only used if TR<5 s) {default: 1.3 s}"
    echo "   extended options for single"
    echo "    --tissref  : Specify tissue reference type: csf, wm, gm or none {default: csf}"
    echo "    --csf      : Manually specify csf mask for calibration"
    echo "    --t1csf    : T1 of CSF (s) - {for default see asl_calib}"
    echo "    --te       : Echo time for the readout (to correct for T2/T2* effect in calibration)"
    echo "    --t2star   : Correct for T2* rather than T2"
    echo "    --t2csf    : T2 of CSF (ms) - {for default see asl_calib}"
    echo "    --t2bl     : T2 of blood (ms) - {for default see asl_calib}"
    echo "    --cref     : Supply a reference image for sensitivity correction"

    echo " Distortion correction using fieldmap (see epi_reg):"
    echo "  requires structural image to be provided"
    echo " --fmap=<image>         : fieldmap image (in rad/s)"
    echo " --fmapmag=<image>      : fieldmap magnitude image - wholehead extracted"
    echo " --fmapmagbrain=<image> : fieldmap magnitude image - brain extracted"
    echo " --echospacing=<val>    : Effective EPI echo spacing (sometimes called dwell time) - in seconds"
    echo " --pedir=<dir>          : phase encoding direction, dir = x/y/z/-x/-y/-z"
    echo " {--nofmapreg}          : do not perform registration of fmap to T1 (use if fmap already in T1-space) "
    echo " Distortion correction using phase-encode-reversed calibration image (TOPUP):"
    echo " --cblip=<image>        : phase-encode-reversed (blipped) calibration image"
    echo " --echospacing=<val>    : Effective EPI echo spacing (sometimes called dwell time) - in seconds"
    echo " --pedir=<dir>          : phase encoding direction, dir = x/y/z/-x/-y/-z"
    echo ""
 
    echo "Partial volume correction"
    echo " --pvcorr    : Do partial volume correction"
    echo "  PV estimates will be taken from:"
    echo "   fsl_anat dir (--fslanat), if supplied"
    echo "   exising fast segmentation (--fastsrc), if supplied"
    echo "   FAST segmenation of structural (if using -s and --sbet)"
    echo "   User supplied PV estimates (--pvgm, --pvwm)"   
    echo "   --pvgm    : Partial volume estimates for GM"
    echo "   --pvwm    : Partial volume estimates for WM"

    echo " Epochs "
    echo " --elen      : Length of each epoch in TIs"
    echo " --eol       : Overlap of each epoch in TIs- {deafult: 0}"
    echo ""
    echo " Miscellaneous "
    echo " --model-options=<file>  : File containing additional model options to be passed to BASIL/Fabber"
    echo "                           This is an advanced setting for model-specific options ONLY"
    echo "                           Do NOT include any standard oxford_asl options here" 
    echo ""
    echo " Notes:"
    echo " Input data - Any combination of label (tag) control images is accepted, see asl_file for more detailed"
    echo "              usage of the input options"
    echo " Analysis  -  If only one TI is specified then the following options are set:"
    echo "              --fixbat --fixbolus --artoff --fulldata"
    echo "              White Paper mode - to conform to the 'white paper' the follow options are also set:"
    echo "              --t1=1.65 --exch=simple --cmethod=voxel"
    echo " Registration - Results are saved in native space by default in case you need to revisit this."
    echo "                By default the perfusion image is used with BBR for the final registration"
    echo "                An inital registration is performed using mean of the ASL data"
    echo "                An alternative base image for (inital) registration can be supplied with --regfrom"
    echo "                Final (BBR) registration can be turned off using --finalonly"
    echo "                For custom registration: use asl_reg with native space results."
    echo " Calibration - Performed using asl_calib using CSF as a reference ('longtr' mode) where structural image is supplied"
    echo "               Voxelwise calibration is performed in 'white paper' mode or in the absence of structural image"
    echo "               For custom calibration: do not set M0 image and then use asl_calib separately"
    echo " Masking - for processing purposes a brain mask is applied to the data, this will be"
    echo "            derrived from (in order of preference):"
    echo "            > Brain extracted structural and (inital) registration"
    echo "            > mean ASL data"
    echo "            > 'regfrom' image if supplied"

}

def output(basil_name, output_name, subdir):
    if nativeout:
        if [ ! -d  $outdir/native_space/$subdir ]; then mkdir $outdir/native_space/$subdir; fi
        imcp $tempdir/$subdir/$param $outdir/native_space/$subdir/$parname
    if structout:
        if [ ! -d  $outdir/struct_space/$subdir ]; then mkdir $outdir/struct_space/$subdir; fi
        flirt -in $tempdir/$subdir/$param -applyxfm -init $tempdir/asl2struct.mat -ref $tempdir/struc -out $outdir/struct_space/$subdir/$parname
    if stdout:
        if [ ! -d  $outdir/std_space/$subdir ]; then mkdir $outdir/std_space/$subdir; fi
        if [ ! -z $warp ]; then
        applywarp --in=$tempdir/$subdir/$param --out=$outdir/std_space/$subdir/$parname --ref=$std --premat=$tempdir/asl2struct.mat --warp=$warp
        elif [ ! -z $trans ]; then
        flirt -in $tempdir/$subdir/$param -applyxfm -init $tempdir/asl2std.mat -ref $std -out $outdir/std_space/$subdir/$parname
        else
        echo "ERROR: cannot do standard space out - neither warp or transformation matrix found"

def output_masked(param_name, subdir, mask):
    # Function to output images having been masked
    # currently we only do this in native space
    if nativeout:
    	fslmaths $outdir/native_space/$subdir/$parname -mas $tempdir/${maskname}mask $outdir/native_space/$subdir/${parname}_masked

def calibrate(basil_name, output_name, moval, multiplier, subdir):
    fslmaths  $tempdir/$subdir/$param -div $Moval -mul $multiplier $tempdir/$subdir/${param}_calib 
    Output ${param}_calib ${parname}_calib $subdir

def report(param, subdir, masktype):
    if pvexist:
    	# generate text reports on parameters - the parameter must have been output first for this to work
	    #NB we only do this is the PVE are available (and thus the reqd masks will exist)

        repval=`fslstats $outdir/native_space/$subdir/$parname -k $tempdir/${masktype}mask_pure -m`
        echo $repval > $outdir/native_space/$subdir/${parname}_${masktype}_mean.txt
        Log "Mean $parname in $masktype is $repval"

def normalise(param, subdir, masktype)
    if pvexist:
        # also output the perfusion images normalised by the mean mask value - the parameter must have been output first for this to work
        #NB we only do this is the PVE are available (and thus the reqd masks will exist)
        
        # get normalization from reported value in the output directory
        normval=`cat $outdir/native_space/$subdir/${parname}_${masktype}_mean.txt`
        
        if stdout:
            fslmaths $outdir/std_space/$subdir/$parname -div $normval $outdir/std_space/$subdir/${parname}_norm 
        if nativeout:
            fslmaths $outdir/native_space/$subdir/$parname -div $normval $outdir/native_space/$subdir/${parname}_norm
        if structout:
            fslmaths $outdir/struct_space/$subdir/$parname -div $normval $outdir/struct_space/$subdir/${parname}_norm 

def normalise_var(param, subdir, masktype):
    if pvexist:
        # normalisaiton for a variance image

        # get normalization from reported value in the output directory
        normval=`cat $outdir/native_space/$subdir/${parname}_${masktype}_mean.txt`
        #need to square the value as we are outputting a variance
        normval=`echo "$normval * $normval" | bc`
        
        if stdout:
            fslmaths $outdir/std_space/$subdir/${parname}_var -div $normval $outdir/std_space/$subdir/${parname}_var_norm 
        if nativeout:
            fslmaths $outdir/native_space/$subdir/${parname}_var -div $normval $outdir/native_space/$subdir/${parname}_var_norm
        if structout:
            fslmaths $outdir/struct_space/$subdir/${parname}_var -div $normval $outdir/struct_space/$subdir/${parname}_var_norm 

def registration(regbase, transopt, distout):
    echo "Performing registration"
    regbase=$1 #the i/p to the function is the image to use for registration
    transopt=$2 # other options to pass to asl_reg
    distout=$3 # we want to do distortion correction and save in the subdir distout
    
    extraoptions=" "
    if [ ! -z $lowstrucflag ]; then
	extraoptions=$extraoptions"-r $tempdir/lowstruc"
    fi
    if [ ! -z $debug ]; then
	extraoptions=$extraoptions" --debug"
    fi
    
    #if [ ! -z $reginit ]; then
    #    extraoptions=$extraoptions" -c $reginit"
    #fi
    
    if [ -z $distout ]; then
	# normal registration
	$asl_reg -i $regbase -o $tempdir -s $tempdir/struc --sbet $tempdir/struc_bet $transopt $extraoptions

	if [ ! -z $trans ]; then
	    # compute the transformation needed to standard space if we have the relvant structural to standard transform
	    convert_xfm -omat $tempdir/asl2std.mat -concat $trans $tempdir/asl2struc.mat
	fi
	    
    else
	# registration for distortion correction
	fmapregstr=""
	if [ ! -z $nofmapreg ]; then
	    fmapregstr="--nofmapreg"
	fi
	$asl_reg -i $regbase -o $tempdir/$distout -s $tempdir/struc --sbet $tempdir/struc_bet $transopt $extraoptions --fmap=$tempdir/fmap --fmapmag=$tempdir/fmapmag --fmapmagbrain=$tempdir/fmapmagbrain --pedir=$pedir --echospacing=$echospacing $fmapregstr
    fi


Calibration() {
 echo "Calculating M0a - calling ASL_CALIB"
    extraoptions=""
    if [ ! -z $debug ]; then
	extraoptions=$extraoptions" --debug"
    fi

    #if [ ! -z $cref ]; then
	# pass calibration reference image to asl_calib
	#extraoptions=$extraoptions" --cref $tempdir/cref"
    if [ ! -z $senscorr ]; then
	    # use a sensitivity iamge from elsewhere
	    Log "Sensitivity image $outdir/native_space/sensitivity being loaded into asl_calib"
	    extraoptions=$extraoptions" --isen $outdir/native_space/sensitivity"
    fi

    if [ -z $te ]; then
	#by default assume TE is zero
	te=0
    fi

    if [ ! -z $t2star ]; then
	# tell asl_calib to correct for T2* rather than T2
	extraoptions=$extraoptions" --t2star"
    fi

    if [ ! -z $tissref ]; then
	# Specify reference tissue type
	extraoptions=$extraoptions" --tissref $tissref"
    fi

    if [ ! -z $t1csf ]; then
	# supply the T1 of csf
	extraoptions=$extraoptions" --t1r $t1csf"
    fi

    if [ ! -z $t2csf ]; then
	# Supply the T2(*) of CSF
	extraoptions=$extraoptions" --t2r $t2csf"
    fi

    if [ ! -z $t2bl ]; then
	# Supply the T2(*) of blood
	extraoptions=$extraoptions" --t2b $t2bl"
    fi

    if [ ! -z $debug ]; then
	#run asl_calib in debug mode
	extraoptions=$extraoptions" --debug"
    fi

    # setup the main options that we will pass to aslcalib regardless of whether we are auot generating reference mask
    maincaliboptions="--cgain $cgain --te $te --tr $tr"

    if [ -z $csfflag ]; then
    # call asl_calib in normal (auto csf) mode

    # use low res structural for auto generation of csf mask if availible
    # otherwise just use structural image
#	if [ -z $lowstrucflag ]; then
#	    usestruc=$tempdir/struc_bet
#	    usetrans=$tempdir/asl2struct.mat
#	else
#	    usestruc=$tempdir/lowstruc_bet
#	    usetrans=$tempdir/asl2lowstruct.mat
#	fi

	usestruc=$tempdir/struc_bet
	usetrans=$tempdir/asl2struct.mat

	if [ ! -z $fasthasrun ]; then
	    # we have already run FAST so we can pass the PVE for CSF to asl_calib (to save running FAST again)
	    extraoptions=$extraoptions" --refpve $tempdir/pvcsf_struct"
	fi
   
	$asl_calib -c $calib -s $usestruc -t $usetrans -o $outdir/calib --bmask $tempdir/mask --osen $outdir/native_space/sensitivity $maincaliboptions $extraoptions 

    else
    # a manual csf mask has been supplied
	$asl_calib -c $calib -m $csf -o $outdir/calib --bmask $tempdir/mask --osen $outdir/native_space/sensitivity $maincaliboptions $extraoptions
    fi
}

Dobasil() {
# inputs: datafile tempdir_subdir initmvn

if [ -z $fast ]; then
    fast=""
else 
    fast="--fast $fast"
fi

Log "Run time basil options:"
Log "$basil_options"
Log "---"

if [ ! -z $3 ]; then
    # we are being supplied with an intial MVN - pass to BASIL
    initmvn="--init $3"
    Log "Initial MVN for BASIL is: $3"
else
    initmvn=""
fi

$basil -i $1 -o $2/basil -m $tempdir/mask -@ $2/basil_options.txt $fast $initmvn $basil_options


# work out which is the final step from BASIL
finalstep=`ls -d $2/basil/step? | sed -n '$ p'`
Log "Using BASIL step $finalstep"

# extract images from BASIL results (and throw away values below zero)
fslmaths ${finalstep}/mean_ftiss -thr 0 $2/ftiss
if [ ! -z $senscorr ]; then
# sensitivity correction
    fslmaths $2/ftiss -div $outdir/native_space/sensitivity $2/ftiss
fi

if [ -z $fixbat ]; then
    fslmaths ${finalstep}/mean_delttiss -thr 0 $2/delttiss
fi
if [ -z $artoff ]; then
    fslmaths ${finalstep}/mean_fblood -thr 0 $2/fblood
    if [ ! -z $senscorr ]; then
# sensitivity correction
	fslmaths $2/fblood -div $outdir/native_space/sensitivity $2/fblood
    fi
fi

#Partial volume correction - sort out basil results when PV corrected
if [ ! -z $pvcorr ]; then
    fslmaths ${finalstep}/mean_fwm -thr 0 $2/ftisswm
    if [ ! -z $senscorr ]; then
        # sensitivity correction
	fslmaths $2/ftisswm -div $outdir/native_space/sensitivity $2/ftisswm
    fi
    if [ -z $fixbat ]; then
	fslmaths ${finalstep}/mean_deltwm -thr 0 $2/deltwm
    fi

fi

if [ ! -z $varout ]; then
#get varainces out of finalMVN
    fabber_var -d ${finalstep} -m $tempdir/mask
# do correction of negative values
    fslmaths ${finalstep}/var_ftiss -bin -add 1 -uthr 1 -mul 1e12 -add ${finalstep}/var_ftiss $2/var_ftiss
    if [ ! -z $senscorr ]; then
# sensitivity correction
    fslmaths $2/var_ftiss -div $outdir/native_space/sensitivity -div $outdir/native_space/sensitivity $2/var_ftiss
fi
    if [ -z $fixbat ]; then
	fslmaths ${finalstep}/var_delttiss -bin -add 1 -uthr 1 -mul 1e12 -add ${finalstep}/var_delttiss $2/var_delttiss
    fi
fi

#copy the final MVN to the temp directory for future use
imcp ${finalstep}/finalMVN $2/finalMVN
cp ${finalstep}/paramnames.txt $2/paramnames.txt


}

Dooutput() {
# Do all the outputs - using the supplied subdirectiory of the results

if [ -z $1 ]; then
    subdir=/ #need a default 'empty' value for this
else
    subdir=$1
fi

# perfusion
Output ftiss perfusion $subdir
Report perfusion $subdir gm
Normalise perfusion $subdir gm

# arrival
if [ -z $fixbat ]; then
    Output delttiss arrival $subdir
    Report arrival $subdir gm
fi
# aBV
if [ -z $artoff ]; then
    Output fblood aCBV $subdir
fi

# white matter values
if [ $subdir = "pvcorr" ]; then
    Output ftisswm perfusion_wm $subdir
    Report perfusion_wm $subdir wm
    Normalise perfusion_wm $subdir wm
    if [ -z $fixbat ]; then
	Output deltwm arrival_wm $subdir
	Report arrival_wm $subdir wm
    fi
    
else 
    Report perfusion $subdir wm
    if [ -z $fixbat ]; then
	Report arrival $subdir wm
    fi
fi

# Masked results (PVcorr)
if [ $subdir = "pvcorr" ]; then
    OutputMasked perfusion $subdir gm
    OutputMasked perfusion_wm $subdir wm
    if [ -z $fixbat ]; then
	OutputMasked arrival $subdir gm
	OutputMasked deltwm $subdir wm
    fi
fi

#Optionally provide variance results
if [ ! -z $varout ]; then
    Output var_ftiss perfusion_var $subdir
    Normalise_var perfusion $subdir gm
    if [ -z $fixbat ]; then
    Output var_delttiss arrival_var $subdir
    fi
    
fi

# calibrated results
if [ ! -z $calibflag ]; then
    if [ $cmethod = 'single' ]; then
	malpha=`echo "$Mo * $alpha" | bc` #include the inversion efficiency when we do the final calibration
    elif [ $cmethod = 'voxel' ]; then
	fslmaths $outdir/calib/M0 -mul $alpha $tempdir/malpha
	malpha=$tempdir/malpha
    fi

    Calibrate ftiss perfusion $malpha 6000 $subdir
    Report perfusion_calib $subdir gm
   
    if [ $subdir = "pvcorr" ]; then
	OutputMasked perfusion_calib $subdir gm
	Calibrate ftisswm perfusion_wm $malpha 6000 $subdir
	Report perfusion_wm_calib $subdir wm
	OutputMasked perfusion_wm_calib $subdir wm
    else
	Report perfusion_calib $subdir wm
    fi

    if [ ! -z $varout ]; then
	if [ $cmethod = 'single' ]; then
	    Mosq=`echo "$Mo * $Mo * $alpha * $alpha" | bc` #include the inversion efficiency when we do the final calibration
	elif [ $cmethod = 'voxel' ]; then
	    fslmaths $outdir/calib/M0 -mul $outdir/calib/M0 -mul $alpha -mul $alpha $tempdir/mosq
        Mosq=$tempdir/mosq
	fi
	
	Calibrate var_ftiss perfusion_var $Mosq 36000000 $subdir
    fi

    if [ -z $artoff ];then
        # output aCBV as a percentage
	    Calibrate fblood aCBV $malpha 100 $subdir
    fi
fi

# advanced output
if [ ! -z $advout ]; then
    if [ ! -d  $outdir/advanced/$subdir ]; then mkdir $outdir/advanced/$subdir; fi
    imcp $tempdir/$subdir/finalMVN $outdir/advanced/$subdir/finalMVN
   cp $tempdir/$subdir/paramnames.txt $outdir/advanced/$subdir/paramnames.txt
fi

}

Log() {
# save text to log, optionally also send to terminal
    echo $1 >> $log
    if [ $verbose -gt 1 ]; then
	echo $1
    fi
}

Warn() {
    # save a warning to the log and echo to the terminal
    echo "WARNING: $1"
    echo "WARNING: $1" >> $log
}

# deal with options

if [ -z $1 ]; then
    Usage
    exit 1
elif [ $1 = "--more" ]; then
    Usage
    Usage_extended
    exit 1
fi

#basil=basil
#asl_reg=asl_reg
#asl_calib=asl_calib

basil=basil
asl_reg=asl_reg
asl_calib=asl_calib

# defaults that (boolean) command line options can overide
spatial=1; # we always use spatial priors, use --spatial=off to turn off.
finalreg=1; # we always try to refine the registration using the perfusion image (Registration 2)
fixbolus=undef; # the default for this is determined by other command line parameters.
edgecorr=1; # we do edge correction with the voxelwise calibration method by default

# parse command line here
until [ -z $1 ]; do

# look at this option and determine if has an argument specified by an =
option=`echo $1 | sed s/=.*//`
arg="" #specifies if an argument is to be read from next item on command line (=1 is is when = is used)
if [ $option = $1 ]; then
# no argument to this command has been found with it (i.e. after an =)
# if there is an argument it will be the next option
    argument=$2
else
    arg=1
    argument=`echo $1 | sed s/.*=//`
fi
takeargs=0;boolarg="";isbool="";
    case $option in
	-o) outflag=1 outdir=$argument
	    takeargs=1;;
	-i) inflag=1 infile=$argument #input/data file
	    takeargs=1;;
	--iaf) iaf=$argument # input asl format (asl_file syntax)
	       takeargs=1;;
	--ibf) ibf=$argument # input block format (asl_file syntax)
	       takeargs=1;;
	--rpts) rpts=$argument # the number of repeats at each TI (when --ibf=tis) - to be passed to asl_file
		takeargs=1;;
	-c) calibflag=1 calib=$argument #calibration image
	    takeargs=1;;
	--wp) whitepaper=1; # operate in 'white paper' mode
	    ;;
	-s) strucflag=1  #NOTE: use strucflag to determin if structural information (in any form) has been provided
	    struc=$argument # strucutral image (not BETed)
	    takeargs=1;;
	--sbrain) strucbet=$argument # user supplied BETed structural
		  takeargs=1;;
	--fslanat) strucflag=1;
		   fslanat=$argument # user supplied fslanat dir (overrides the structural image inputs)
		   takeargs=1;;
	--fastsrc) strucflag=1;
		   fastsrc=$argument # user supplied FAST results (this is the stub of the filenames)
		   takeargs=1;;
	-r) lowstrucflag=1 lowstruc=$argument #low resolution structural image
	    takeargs=1;;
	-t) transflag=1;
	    trans=$argument;
	    stdout=1;
	    takeargs=1;;
	-S) stdflag=1 std=$argument
	    takeargs=1;;
	--warp) transflag=1;
		warp=$argument; #structural to standard warp
		stdout=1;
		takargs=1;;
	-m) mask=$argument
	    takeargs=1;;
	--mc) isbool=1; # do motion correction using mcflirt
	      boolarg=moco;
	      ;;
	--tis) tis=$argument
	    takeargs=1;;
	--bolus) boluset=1 boluslen=$argument
	    takeargs=1;;
	--bat) bat=$argument
	    takeargs=1;;
	--batsd) batsd=$argument
	    takeargs=1;;
	--slicedt) slicedt=$argument
	    takeargs=1;;
	--sliceband) sliceband=$argument
	    takeargs=1;;
	--fa) fa=$argument
	    takeargs=1;;
	--t1) t1set=$argument # the T1 of tissue to be used in kinetic model
	    takeargs=1;;
	--t1b) t1bset=$argument
	       takeargs=1;;
	--t1im) t1im=$argument # A T1 (of tissue) image
		takeargs=1;;
	--noiseprior) noiseprior=1
	    ;;
	--noisesd) noisesd=$argument
	    takeargs=1;;
	--cmethod) cmethod=$argument
	    takeargs=1;;
	--tissref) tissref=$argument
	    takeargs=1;;
	--edgecorr) isbool=1;
		    boolarg=edgecorr;
		    ;;
	--csf) csfflag=1 csf=$argument
	    takeargs=1;;
	--cref) cref=$argument; senscorr=1;
	    takeargs=1;;
	--isen) isen=$argument; senscorr=1;
	    takeargs=1;;
	--senscorr) needseg=1; senscorr=1; #disbale 
	    ;;
	--M0) M0=$argument; calibflag=1;
	    takeargs=1;;
	--t1t) t1tset=$argument; #the T1 of tissue to be used in calibration
	    takeargs=1;;
	--tr) tr=$argument
	    takeargs=1;;
	--te) te=$argument #supply the echo time for calibration correction for T2
	    takeargs=1;;
	--t2star) t2star=1 #do calibration with T2* rather than T2
	    ;;
	--t1csf) t1csf=$argument #custom T1 for CSF
	    takeargs=1;;
	--t2csf) t2csf=$argument #custom T2 for CSF
	    takeargs=1;;
	--t2bl) t2bl=$argument #custom T2 of blood
	    takeargs=1;;
	--regfrom) regfromflag=1 regfrom=$argument
		   takeargs=1;;
	--finalreg) isbool=1; # To turn off the final registration step that uses the perfusion image itself (with BBR) - helpful is the perfusion image is poor and thus not a good basis for registration
		    boolarg=finalreg;
		    ;;
	--asl2struc) asl2struc=$argument
	    takeargs=1;;
	--cgain) cgain=$argument
	    takeargs=1;;
	--alpha) alpha=$argument
	    takeargs=1;;
	--zblur) zblur=1
	    ;;
	--structout) structout=1
	    ;;
	--advout) advout=1
	    ;;
	--spatial) #spatial=1
		   isbool=1;
		   boolarg=spatial;
	    ;;
	--infert1) infert1=1
	    ;;
	--artoff) artoff=1
	    ;;
	--artsupp) artoff=1 #this does same job as --artoff, but is explicitly linked to vascular crushers in the data
	    ;;
	--fixbat) fixbat=1
	    ;;
	--fixbolus) isbool=1
		    boolarg=fixbolus;
	    ;;
	--casl) casl=1
		;;
	--disp) disp=$argument
	    takeargs=1;;
	--exch) exch=$argument
	    takeargs=1;;
	--pvcorr) pvcorr=1
	    ;;
	--pvgm) pvgm=$argument
	    takeargs=1;;
	--pvwm) pvwm=$argument
	    takeargs=1;;
	--fulldata) fulldata=1
	    ;;
	--elen) epoch=1 elen=$argument
	    takeargs=1;;
	--eol) eol=$argument
	       takeargs=1;;
	--fast) fast=2 #do a one step analysis (NB generally a good idea to have spatial on for this option)
		;;

	# fieldmap/distorition correction related arguments
	--fmap) fmap=$argument
		takeargs=1;;
	--fmapmag) fmapmag=$argument
		   takeargs=1;;
	--fmapmagbrain) fmapmagbrain=$argument
			takeargs=1;;
	--echospacing) echospacing=$argument
		       takeargs=1;;
	--pedir) pedir=$argument
		 takeargs=1;;
	--nofmapreg) isbool=1
		     boolarg=nofmapreg
		     ;;
	--cblip) cblip=$argument #blip reversed calibration image
		 takeargs=1;; 
	# 
	--model-options) model_options=$argument
	    takeargs=1;;
	--verbose) verbose=$argument
	    takeargs=1;;
	--debug) debug=1
	    ;; 
	--devel) devel=1
	    ;;
	--version) Version
	    ;;
	*)  #Usage
	    echo "Error! Unrecognised option on command line: $option"
	    echo ""
	    exit 1;;
    esac


    # sort out a shift required by a command line option that takes arguments
    if [ -z $arg ]; then
	# an argument has been supplied on the command NOT using an =
	if [ $takeargs -eq 1 ]; then
	    shift;
	fi
    fi
    
    if [ ! -z $isbool ]; then
	    # this is an (explicit) boolean setting
	if [ ! -z $arg ]; then
	    # an argument has been supplied on the command using an =
	    # set the variable based on the argument
	    case $argument in
		on) eval $boolarg=1
		    ;;
		off) eval $boolarg=""
		     ;;
		1) eval $boolarg=1
		   ;;
		0) eval $boolarg=""
		   ;;
		*)  Usage
		    echo "Error! Unrecognised setting for boolean option: $1"
		    echo ""
		    exit 1;;
	    esac
	else
	    # no argument has been suppled with this command (NOTE that you cannot supply an arugment to a bool option without an =)
	    # this sets the variable to true
	    eval $boolarg=1;
	fi
    fi


    # shift to move on to next parameter
    shift
done

nativeout=1 #we always keep the native space images!!
varout=1 # we always output the variance images

if [ -z $verbose ]; then
    verbose=1
fi

# deal with the temporary directory
tmpbase=`tmpnam`
tempdir=${tmpbase}_ox_asl
mkdir $tempdir

echo "#FABBER options created by Oxford_asl" > $tempdir/basil_options.txt

# deal with default output format
if [ ! -z $transflag ]; then
   #if transformation matrix included then output in std space
    stdout=1;
    if [ -z $strucflag ]; then
	echo "ERROR: Structural image is required along with transformation matrix to output results in standard space"
	exit 1
    fi
else
    if [ ! -z $strucflag ]; then
	# else-if strucutral image included output in structural space
	structout=1;
    else
	#else output in native space
	nativeout=1;
    fi
fi

echo "OXFORD_ASL - running"
echo "Version: @GIT_SHA1@ @GIT_DATE@"

# set the output directory here if not specified
if [ -z $outflag ]; then
    echo "Ouput being placed in input directory"
    outdir=`pwd`;
fi

# Start by looking for the output directory (and create if need be)
if [ ! -d $outdir ]; then
  echo "Creating output directory"
  mkdir $outdir;
fi

# save command line to logfile
log=$outdir/logfile
echo $# > $log

#check required inputs are present
if [ -z $inflag ]; then
    echo "ERROR: no input file specified"
    exit 1
else
    if [ `imtest $infile` -eq 0 ]; then
	echo "ERROR: $infile is not an image/has not been found"
	exit 1
    fi
fi
Log "Input file: $infile"

if [ ! -z $strucflag ]; then
    if [ ! -z $struc ]; then
	if [ `imtest $struc` -eq 0 ]; then
	    echo "ERROR: $struc is not an image/has not been found"
	    exit 1
	fi
	Log "Structural image: $struc"
    fi
    
fi




if [ ! -z $lowstruc ]; then
    if [ `imtest $lowstruc` -eq 0 ]; then
	echo "ERROR: $lowstruc is not an image/has not been found"
	exit 1
    fi
    Log "Low res. structural image: $lowstruc"
fi


# Setup option outputs - main subdirectories and anything that would be common to all epochs
if [ ! -z $nativeout ] && [ ! -d $outdir/native_space ]; then
    echo "Saving results in natve (ASL aquisition) space to $outdir/native_space"
    mkdir $outdir/native_space
fi
if [ ! -z $structout ] && [ ! -d $outdir/struct_space ]; then
    echo "Saving results in structural space to $outdir/struct_space"
    mkdir $outdir/struct_space
fi
if [ ! -z $advout ] && [ ! -d $outdir/advanced ]; then
echo "Saving advanced outputs"
    mkdir $outdir/advanced
fi

### Command line parameter interactions
# white paper mode - this overrieds defaults, but can be overwritten (below) by command line specification of individual parameters
if [ ! -z $whitepaper ]; then
    Log "Analysis in white paper mode"
    t1set=1.65
    cmethod=voxel
    bat=0 # the white paper model ignores BAT
    # note that other things related to the model will be set by single TI mode below
fi

# bolus duration inference
# if we are doing CASL then fix the bolus duration, except where the user has explicitly told us otherwise
if [ $fixbolus = "undef" ]; then
    # fixbolus is to take its default value
    if [ ! -z $casl ]; then
	fixbolus=1;
    else
	fixbolus="";
    fi
fi

### End of Command line parameter interactions

# general pre-processing
echo "Pre-processing"
if [ ! -z $fslanat ]; then
    # we are being supplied with an fslanat directory
    # copy over the structural and brain extracted strucutral so that we can use them
    if ls $fslanat/T1_biascorr.* 1> /dev/null 2>&1; then
	Log "Using structural images (bias corrected) from fsl_anat: $fslanat"
	imcp $fslanat/T1_biascorr $tempdir/struc
	imcp $fslanat/T1_biascorr_brain $tempdir/struc_bet
    else
	Log "Using structural images from fsl_anat: $fslanat"
	imcp $fslanat/T1 $tempdir/struc
	imcp $fslanat/T1_biascorr_brain $tempdir/struc_bet
    fi
    
    # use the registration to standard space - if it is there
    if [ -e $fslanat/T1_to_MNI_nonlin_coeff.nii.gz ]; then
        stdout=1; transflag=1;
	warp=$fslanat/T1_to_MNI_nonlin_coeff.nii.gz
    elif [ -e $fslanat/T1_to_MNI_lin.mat ]; then
        stdout=1; transflag=1;
	trans=$fslanat/T1_to_MNI_lin.mat
    fi
    
elif [ ! -z $struc ]; then
    fslmaths $struc $tempdir/struc
    Log "Structural image is: $struc"
    if [ -z $strucbet ]; then
       #bet the structural for calibration and registration
	bet $struc $tempdir/struc_bet
	Log "BET on structural image"
    else
	fslmaths $strucbet $tempdir/struc_bet
    fi
fi

if [ ! -z $transflag ]; then
    # deal with Standard brain image
    if [ -z $stdflag ]; then
	std=${FSLDIR}/data/standard/MNI152_T1_2mm
    fi
    Log "Standard brain is: $std"

    if [ ! -z $warp ]; then
	Log "Structural to standard transformation warp: $warp"
    elif [ ! -z $trans ]; then
	Log "Structural to standard transformation matrix: $trans"
    fi
fi

if [ ! -z $lowstrucflag ]; then
    fslmaths $lowstruc $tempdir/lowstruc
## bet the low res. struc (if present)
#    bet $lowstruc $tempdir/lowstruc_bet
#    Log "BET on low res. structural image"
fi

# standard pre-processing of calibration image
if [ ! -z $calib ]; then
    tsize=`fslinfo $calib | grep "^dim4" | sed 's:dim4[ ]*::'`
    if [ $tsize -gt 1 ]; then
        #cut - throw away first volume
	Log "Removing first volume of calibration time series - to ensure data is in steady state"
	tsize=`expr $tsize - 1`
	fslroi $calib $tempdir/calib 1 $tsize

	if [ ! -z $moco ]; then
	    #motion correction
	    mcflirt -in $tempdir/calib -o $tempdir/calib
	fi
	# take the mean
	fslmaths $tempdir/calib -Tmean $tempdir/calib
    else
	fslmaths $calib $tempdir/calib
    fi
fi

# same thing for cref image
if [ ! -z $cref ]; then
    tsize=`fslinfo $cref | grep "^dim4" | sed 's:dim4[ ]*::'`
    if [ $tsize -gt 1 ]; then
        #cut - throw away first volume
	Log "Removing first volume of calibration reference time series - to ensure data is in steady state"
	tsize=`expr $tsize - 1`
	fslroi $cref $tempdir/cref 1 $tsize

	if [ ! -z $moco ]; then
	    #motion correction
	    mcflirt -in $tempdir/cref -o $tempdir/cref
	fi
	# take the mean
	fslmaths $tempdir/cref -Tmean $tempdir/cref
    else
	fslmaths $cref $tempdir/cref
    fi
fi

# same thing for cblip image
if [ ! -z $cblip ]; then
    tsize=`fslinfo $cblip | grep "^dim4" | sed 's:dim4[ ]*::'`
    if [ $tsize -gt 1 ]; then
        #cut - throw away first volume
	Log "Removing first volume of blipped calibration time series - to ensure data is in steady state"
	tsize=`expr $tsize - 1`
	fslroi $cblip $tempdir/cblip 1 $tsize

	if [ ! -z $moco ]; then
	    #motion correction
	    mcflirt -in $tempdir/cblip -o $tempdir/cblip
	fi
	# take the mean
	fslmaths $tempdir/cblip -Tmean $tempdir/cblip
    else
	fslmaths $cblip $tempdir/cblip
    fi
    # NOTE cblip is still wholehead, we dont need it masked
fi

# read in ASL data
imcp $infile $tempdir/asldata # this is the MAIN data that we will reflect any corrections applied
# take a copy that will not be subject to any subsequent corrections
imcp $tempdir/asldata $tempdir/asldata_orig

### Motion Correction (main)
# note motion correction within calibration data is done above
if [ ! -z $moco ]; then
    echo "Motion Correction"
    if [ ! -z $calib ]; then
	# we use the calibration image as our reference for motion correction - since this will be most consistent if the data has a range of different TIs and background suppression etc
	# this also removes motion effects between asldata and calibration image
	Log "Motion correction to calibration image"
	mcflirt -in $tempdir/asldata -out $tempdir/asldata -r $tempdir/calib -mats

	# to reduce interpolation of the ASL data change the transformations so that we end up in the space of the central volume of asldata
	# Extract the middle transformation
	middlemat=`ls $tempdir/asldata.mat/MAT_* | awk '{ lines[NR]=$0; } END { print lines[int(NR/2)+1] }'`
	convert_xfm -omat $tempdir/calib2asl.mat -inverse $middlemat
	# convert all the transofmrations
	for mat in `ls $tempdir/asldata.mat/MAT_*`; do
	    convert_xfm -omat $mat -concat $tempdir/calib2asl.mat $mat
	done
	applyxfm4D $tempdir/asldata_orig $tempdir/asldata $tempdir/asldata $tempdir/asldata.mat -fourdigit
	# Convert all calibration images to align with asldata
	flirt -in $tempdir/calib -out $tempdir/calib -ref $tempdir/asldata -init $tempdir/calib2asl.mat -applyxfm
    if [ ! -z $cref ]; then
        flirt -in $tempdir/cref -out $tempdir/cref -ref $tempdir/asldata -init $tempdir/calib2asl.mat -applyxfm
    fi
    if [ ! -z $cblip ]; then
        flirt -in $tempdir/cblip -out $tempdir/cblip -ref $tempdir/asldata -init $tempdir/calib2asl.mat -applyxfm
    fi
    else
	Log "Motion correction to middle volume of ASL data"
	mcflirt -in $tempdir/asldata -out $tempdir/asldata -mats
    fi
    cat $tempdir/asldata.mat/MAT* > $tempdir/asldata.cat # save the motion matrices for distortion correction if reqd
fi

### deal with TIs (as specified on the command line)
count=0
tislist=""
thetis=`echo $tis | sed 's:,: :g'`
#echo $thetis
for ti in $thetis; do
    count=`expr ${count} + 1`
    tislist=`echo $tislist --ti${count}=$ti`
    alltis[`expr ${count} - 1`]=$ti
done
Log "Number of TIs in list: $count"
Log "TIs list: $tislist"
ntis=$count
### End of: Deal with the TIs

### Label-control subtraction (we repeat subtraction after doing distortion correction - when applicable)
# We get data into correct block format for BASIL here
if [ -z $iaf ]; then
    # DEFAULT input ASL format is 'diff' (label-control difference data) - maintains backward compatibility
    iaf="diff"
fi
Log "Input ASL format is: $iaf"
if [ -z $ibf ]; then
    # DEFAULT input block format is 'rpt' (data is as typically acquired) - maintains backward compatibility
    ibf="rpt"
fi
Log "Input block format is: $ibf"

afrptstr=""
if [ $ibf == "tis" ]; then
    if [ ! -z $rpts ]; then
	# the repeats at each TI have been specified
	afrptstr="--rpts=$rpts"

	if [ ! -z $epoch ]; then
	    echo "ERROR: cannot do epochwise analysis when there are not the same number of repeats for each TI"
	    exit 1
	fi
    fi
fi

if [ $iaf = 'diff' ]; then
    # make sure the block format is correct for BASIL
    asl_file --data=$infile --ntis=$ntis --ibf=$ibf $afrptstr --iaf=$iaf --obf=tis --out=$tempdir/diffdata --mean=$tempdir/diffdata_mean
    Log "Label-control difference data provided: $infile"
else
    # create label-control difference data using asl_file - this gets it into the right block form for BASIL (blocks of TIs)
    asl_file --data=$infile --ntis=$ntis --ibf=$ibf $afrptstr --iaf=$iaf --obf=tis --diff --out=$tempdir/diffdata --mean=$tempdir/diffdata_mean
    
    # pull out (label &) control images (NB these will have suffix _even or _odd)  *TODO asl_file should now be able to do suffix of _label and _control, which would be more helpful
    # NOT enabled at the moment - since this is only specifically useful for extensing the calibration options - TODO 
    #asl_file --data=$infile --ntis=$ntis --ibf=$ibf --iaf=$iaf --obf=tis --split --out=$tempdir/asldata --mean=$tempdir/asldata_mean

fi
### End of : Label-control subtraction

### Establish the number of repeats in data - query the diffdata file (that will contain all repeats)
tpoints=`fslinfo $tempdir/diffdata | grep "^dim4" | sed 's:dim4[ ]*::'`

echo "Number of inversion times: $ntis"
echo "Number of timepoints in data: $tpoints"

if [ -z $afrptstr ]; then
    repeats=`expr $tpoints / $ntis`
    echo "Number of repeats in data: $repeats"
else
    repeats=0 #variable number of repeats at each TI - have to handle specially
    ### deal with repeats (as specified on the command line)
    count=0
    rptslist=""
    therpts=`echo $rpts | sed 's:,: :g'`
    for rp in $therpts; do
	count=`expr ${count} + 1`
	rptslist=`echo $rptslist --rpt${count}=$rp`
    done
    Log "RPTs list: $rptslist"
fi
### End of: Establish number of repeats

# Single or Multi TI setup
if [ $ntis -lt 2 ]; then
# single TI data - dont average send to BASIL as-is (helps with noise estimation)
#    Log "Single TI data to be passed to BASIL"
    #datafile=$tempdir/diffdata
    # OPERATE in 'single TI mode'
    artoff=1; fixbolus=1; #fixbat=1; #fast=1; 
    Log "Operating in Single TI mode"
    singleti=1;
    
#elif [ $repeats -gt 1 ]; then
 #   if [ -z $fulldata ]; then
        # take the mean over the TIs for faster analysis
#	Log " Multi TI data, mean is being taken at each TI to pass to BASIL"
#	datafile=$tempdir/diffdata_mean
#	repeats=1
 #   else
#	Log "Multi TI data, all data passed to BASIL for analysis"
 #       datafile=$tempdir/diffdata
 #   fi
#else
    # if there is only one repeat it just gets passed stright to BASIL
#    echo " Multi-TI data (single measurment at each TI) to be passed to BASIL" >> $log
    #    datafile=$tempdir/diffdata
fi

# finish filling the alltis array - this is for epochwise analysis - this only works when there are the same number of repeats at each TI
# Epochwise analysis presume that the data was acquired in blocks of all TIs (even if that is not how is supplied to oxford_asl)
# Otherwise epoch analysis doens't make sense
# NB: we use the tislist and numerb of repeats for BASIl for the conventional perfusion image
for ((r=1; r<$repeats; r++)); do
    for ((i=0; i<$ntis; i++)); do
	idx=`expr $r \* $ntis + $i`
	alltis[$idx]=${alltis[$i]}
    done
done
echo ${alltis[*]}
Log `echo ${alltis[*]}`

# take mean of the asl data as we might need this later
fslmaths $tempdir/asldata -Tmean $tempdir/meanasl
# generate a perfusion-weighted image by taking the mean over all TIs
fslmaths $tempdir/diffdata_mean -Tmean $tempdir/pwi

### Registration (1/2)
# Make sure we have some form of transformation between the ASL data and the structural (if that has been supplied)
# only 'initial' step in asl_reg is used here
register=0
if [ ! -z $strucflag ]; then # if structural image has not been suppled then skip the registration
    register=1
    if [ ! -z $asl2struc ]; then # we have been supplied with a transformation matrix - we do not need registration, but we do want to transform the results
	register=0
	Log "Using existing asl to structural transform: $asl2struc"
	cp $asl2struc $tempdir/asl2struct.mat
	convert_xfm -omat $tempdir/struct2asl.mat -inverse $tempdir/asl2struct.mat
    fi
fi

if [ -z $regfrom ]; then
# no regfrom iamge supplied so we will use the mean of the asl timeseries - unless it was diff data
    # NB in the case of really good background suppresion this might not be best option even if raw ASL data has been supplied, in which case a calibration image could be provided to regfrom (or failing that the PWI). We wont force that here as we dont know.
    if [ $iaf = "diff" ] && [ ! -z $calib ]; then
	#if available use calibration image
	bet $tempdir/calib $tempdir/calib_brain 
	regfrom=$tempdir/calib_brain
    else
	# brain extract the meanasl image
	bet $tempdir/meanasl $tempdir/meanasl_brain -f 0.2 #somewhat conservative fraction to avoid erosion
	regfrom=$tempdir/meanasl_brain
    fi
fi

if [ $register -eq 1 ]; then
# registration here using asl_reg (inital only)
    if [ ! -z $regfrom ]; then
	Log "Performing registration"
	Log "Using $regfrom as base for inital registration"

	extraoptions="--mainonly " # to ensure we only do the initil flirt part
	if [ ! -z $lowstrucflag ]; then
	    extraoptions=$extraoptions"-r $tempdir/lowstruc"
	fi

	Registration $regfrom $extraoptions
    fi
    convert_xfm -omat $tempdir/struct2asl.mat -inverse $tempdir/asl2struct.mat
fi
### End of: Registration (1/2)

### Segmentation of structural image - if we have a structural image we ALWAYS ensure we have a segmentation
if [ ! -z $fslanat ]; then
    # we are being supplied with an fslanat directory
    fasthasrun=1 #this means that we have PVE for calibration & PVC purposes
    
    # copy over the things we need and place them using the names used elsewhere
    imcp $fslanat/T1_fast_pve_0 $tempdir/pvcsf_struct #indicate that it is in structural space!
    imcp $fslanat/T1_fast_pve_1 $tempdir/pvgm_struct
    imcp $fslanat/T1_fast_pve_2 $tempdir/pvwm_struct

    if [ ! -z $fslanat/T1_fast_bias ]; then # test to check that there is a bias field here
       Log "Bias field extracted from $fslanat sucessfully"
       imcp $fslanat/T1_fast_bias $tempdir/biasfield_struct
    else
	Log "No Bias field found in $fslanat"
    fi
    
elif [ ! -z $struc ]; then
    # do we have the results from FAST already? If not run it
    if [ -z $fastsrc ]; then
	echo "Segmenting the structural image"
	Log "Segmenting the structural image"
	fast -B -b -o $tempdir/seg -p $tempdir/struc_bet
	fastsrc=$tempdir/seg
    else
	# FAST has been run externally
	Log "Using FAST outputs at: $fastsrc"
    fi
	
    # we are now sure we have FAST outputs
    fasthasrun=1

     # copy over the things we need and place them using the names used elsewhere
    imcp ${fastsrc}_pve_0 $tempdir/pvcsf_struct #indicate that it is in structural space!
    imcp ${fastsrc}_pve_1 $tempdir/pvgm_struct
    imcp ${fastsrc}_pve_2 $tempdir/pvwm_struct

    if [ ! -z ${fastsrc}_bias ]; then # test to see if there is a bias field in the FAST output
	Log "Bias field extracted from ${fastsrc} sucessfully"
	imcp ${fastsrc}_bias $tempdir/biasfield_struct
    else
	Log "No Bias field found with ${fastsrc}"
    fi
     
fi

# some useful preproc to do with FAST outputs
if [ ! -z $fasthasrun ]; then
    # create a tissseg (wmseg) image for BBR in asl_reg
    fslmaths $tempdir/pvwm_struct -thr 0.5 -bin ${tempdir}/tissseg

    if [ ! -z $tempdir/biasfield_struct ]; then
	# transform the bias field and invert to use for sensitivity correction in calibration
	applywarp --ref=$tempdir/asldata --in=$tempdir/biasfield_struct --out=$tempdir/biasfield --premat=$tempdir/struct2asl.mat --super --interp=spline --superlevel=4
    fi

    if [ ! -z $senscorr ]; then
	if [ ! -z $tempdir/biasfield ]; then #make sure we have the biasfield (from above) before attempting this
	    Log "Creating sensitivity map from biasfield"
	    fslmaths $tempdir/biasfield -recip $outdir/native_space/sensitivity
	fi	    
    fi

fi
    
### End of: Segmentation

### Generate mask for ASL data
# sort out the mask for processing the data
if [ -z $mask ]; then
echo "Creating mask"
Log "Automatic mask generation"
# preferred option is to use brain extracted structural
if [ ! -z $strucflag ]; then
    fslmaths $tempdir/struc_bet -bin $tempdir/struc_bet_mask
    flirt -in $tempdir/struc_bet_mask -ref $regfrom -applyxfm -init $tempdir/struct2asl.mat -out $tempdir/mask -interp trilinear
    fslmaths $tempdir/mask -thr 0.25 -bin -fillh $tempdir/mask
    fslcpgeom $regfrom $tempdir/mask
# otherwise use the regfrom image (should already be BETed) - note that regfrom may have been set in the Registration (1/2) section.
elif [ ! -z $regfrom ]; then
    fslmaths $regfrom -bin $tempdir/mask
    Log "Mask generated from regfrom image: $regfrom"
    
# We are unlikey to use these options as regfrom has probably been set above - leave for future reference
# next option is to use betted version of mean M0 calib image as mask
elif [ ! -z $calib ]; then
    bet $tempdir/calib $tempdir/calib_bet
    fslmaths $tempdir/calib_bet -bin $tempdir/mask
    Log "Mask generated from calibration image (post BET)"
 # use the low resolution strucutral image to create mask (ahould already be BETed)
elif [ ! -z $lowstrucflag ]; then
 # resample
    flirt -in $tempdir/lowstruc -applyxfm -init $FSLDIR/etc/flirtsch/ident.mat -out $tempdir/mask -paddingsize 0.0 -interp trilinear -ref $tempdir/asldata
 # make binary
    fslmaths $tempdir/mask -bin $tempdir/mask
    Log "Mask generated from low res. structural"
# otherwise just use mean time series
else
    bet $tempdir/meanasl $tempdir/meanasl -f 0.2 # use a fairly low fraction value to avoid erosion
    fslmaths $tempdir/meanasl -bin $tempdir/mask
    Log "Mask generated from mean time series"
fi
else
# mask has been supplied
    fslmaths $mask -bin $tempdir/mask # just to be sure binarise the mask here
    Log "Using mask: $mask"
fi
### End of: Generate mask

### Distortion Correction
# Do TOPUP if applicable
if [ ! -z $cblip ]; then
    if [ -z $calib ]; then
	echo "WARNING: Cannot do TOPUP on blip-reversed calibration image ($cblip) without correpsonding calibration image"
    elif [ -z $echospacing ] || [ -z $pedir ]; then
	echo "WARNING: Cannot do TOPUP on blip-reversed calibration image without echospacing (dwell time) and pahse encode direction"
    else
	echo "Distortion correction: running topup"
	
        #create topup params
	case $pedir in
	    x)
		echo "1 0 0 $echospacing" > $tempdir/topup_params.txt
		echo "-1 0 0 $echospacing" >> $tempdir/topup_params.txt
		;;
    	    -x)
		echo "-1 0 0 $echospacing" > $tempdir/topup_params.txt
		echo "1 0 0 $echospacing" >> $tempdir/topup_params.txt
		;;
	    y)
		echo "0 1 0 $echospacing" > $tempdir/topup_params.txt
		echo "0 -1 0 $echospacing" >> $tempdir/topup_params.txt
		;;
	    -y)
		echo "0 -1 0 $echospacing" > $tempdir/topup_params.txt
		echo "0 1 0 $echospacing" >> $tempdir/topup_params.txt
		;;
	    z)
		echo "0 0 1 $echospacing" > $tempdir/topup_params.txt
		echo "0 0 -1 $echospacing" >> $tempdir/topup_params.txt
		;;
    	    -z)
		echo "0 0 -1 $echospacing" > $tempdir/topup_params.txt
		echo "0 0 1 $echospacing" >> $tempdir/topup_params.txt
		;;
	esac
    
	# do topup
	fslmerge -t $tempdir/calib_blipped $tempdir/calib $cblip 
	topup --imain=$tempdir/calib_blipped --datain=$tempdir/topup_params.txt --config=b02b0.cnf --out=$tempdir/topupresult --fout=$tempdir/topupresult_fmap
	topupresult=$tempdir/topupresult
    fi
fi

#Fieldmaps
if [ ! -z $topupresult ]; then
#    if [ -e $tempdir/struc.* ]; then
#	# currently DISABLED and applytopup is used with topup results
#	#we will do the distorition correction using epi_reg so that we can merge with motion correction matrices and also get the jacobian
#	# the fieldmap provided is from topup and will be in ASL space
#	# convert ot the correct units of rad/s from Hz
#	fslmaths ${topupresult}_fmap -mul 3.1459 -mul 2 $tempdir/fmap
#	# use the existing registration to get the fieldmap into T1 space
#	flirt -in $tempdir/fmap -out $tempdir/fmap -ref $tempdir/struc -applyxfm -init $tempdir/asl2struct.mat
#	# asl_reg/epi_reg will expect a fieldmap magnitude image (although doesn't really need it in this case) - just use the structural
#	imcp $tempdir/struc $tempdir/fmapmag
#	imcp $tempdir/struc_bet $tempdir/fmapmagbrain
#	nofmapreg=1
#    else
	echo "Distortion Correction using TOPUP"
	# we will use apply topup - this does not do the jacboian magntiude correction - therefore strictly only okay if using voxelwise calibration
	applytopup --imain=$tempdir/calib,$cblip --inindex=1,2 --datain=$tempdir/topup_params.txt --topup=${topupresult} --out=$tempdir/calib --method=jac
	repeatsubtract=1;
	applytopup --imain=$tempdir/asldata --datain=$tempdir/topup_params.txt --inindex=1 --topup=${topupresult} --out=$tempdir/asldata --method=jac #ND using asldata as this has been motion corrected by this point (if requested)
	if [ ! $cmethod="voxel" ]; then
	    echo "WARNING: Using apply_topup this does not correct for magntiude using the jocbian in distortion correction - this is not optimal when not using voxelwise calibration, to avoid this supply structural image(s)"
	fi
    
	if [ ! -z $cref ]; then
	    applytopup --imain=$tempdir/cref --datain=$tempdir/topup_params.txt --inindex=1 --topup=${topupresult} --out=$tempdir/cref --method=jac
#	fi
    fi
elif [ ! -z $fmap ]; then
    # a fieldmap has been provided that needs registration - copy images over
    imcp $fmap $tempdir/fmap
    imcp $fmapmag $tempdir/fmapmag
    imcp $fmapmagbrain $tempdir/fmapmagbrain
fi

if [ -e $tempdir/fmap.* ]; then
    echo "Distortion Correction using asl_reg"
    
    # Do registration to T1 to get distortion correction warp
    # use whatever registration matrix we already have to initialise here 
    distbase=$tempdir/pwi # use the perfusion-weighted image (mean over all TIs) as the best basis we have for registration at this point
    if [ -z $finalreg ]; then
	distbase=$regfrom # use whatever image we have been using for (inital) registration
    fi

    Registration $distbase "-m $tempdir/mask --tissseg $tempdir/tissseg --imat $tempdir/asl2struct.mat --finalonly" distcorr
    
    # generate the correction warp
    convertwarp -r $tempdir/meanasl -o $tempdir/asldist_warp -w $tempdir/distcorr/asl2struct_warp.nii.gz --postmat=$tempdir/distcorr/struct2asl.mat --rel -j $tempdir/distcorr/jacobian_parts
    fslmaths $tempdir/distcorr/jacobian_parts -Tmean $tempdir/distcorr/jacobian
    
    # Now apply the correction to the data.
    # note that we use the orignal data here and apply the motion correction as part of the process
    appremat=""
    if [ ! -z $moco ]; then
	appremat="--premat=$tempdir/asldata.cat"
    fi
    applywarp -i $tempdir/asldata_orig -r $tempdir/meanasl -o $tempdir/asldata $appremat -w $tempdir/asldist_warp --rel --interp=spline --paddingsize=1
    fslmaths $tempdir/asldata -mul $tempdir/distcorr/jacobian $tempdir/asldata
    repeatsubtract=1;
        
    # Now apply the correction to the calibration image
    applywarp -i $tempdir/calib -r $tempdir/calib -o $tempdir/calib -w $tempdir/asldist_warp --rel --interp=spline --paddingsize=1
    fslmaths $tempdir/calib -mul $tempdir/distcorr/jacobian $tempdir/calib
 
    if [ ! -z $cref ]; then
	applywarp -i $tempdir/cref -r $tempdir/calib -o $tempdir/cref -w $tempdir/asldist_warp --rel --interp=spline --paddingsize=1
	fslmaths $tempdir/cref -mul $tempdir/distcorr/jacobian $tempdir/cref
    fi
fi

# Repeat the label-control subtraction on the corrected data
if [ ! -z $repeatsubtract ]; then
    if [ $iaf = 'diff' ]; then
	# make sure the block format is correct for BASIL
	asl_file --data=$tempdir/asldata --ntis=$ntis --ibf=$ibf --iaf=$iaf --obf=tis --out=$tempdir/diffdata --mean=$tempdir/diffdata_mean
    else
	# create label-control difference data using asl_file - this gets it into the right block form for BASIL (blocks of TIs)
	asl_file --data=$tempdir/asldata --ntis=$ntis --ibf=$ibf --iaf=$iaf --obf=tis --diff --out=$tempdir/diffdata --mean=$tempdir/diffdata_mean
    fi
fi
### End of: Distortion Correction

# Mask the calibration images, saving the wholehead images (although currently unused)
if [ ! -z $calib ]; then
    imcp $tempdir/calib $tempdir/calib_wholehead
    fslmaths $tempdir/calib -mas $tempdir/mask $tempdir/calib
fi
if [ ! -z $cref ]; then
    imcp $tempdir/cref $tempdir/cref_wholehead
    fslmaths $tempdir/cref -mas $tempdir/mask $tempdir/cref
fi

# Copy or recalculate the sensitivity map (overwriting any created
# by FAST) if we have a cref image or a sensitivity image has been supplied directly
if [ ! -z $isen ]; then
    # User-supplied sensitivity image
    Warn "User supplied sens image"
    fslmaths $isen -mas $tempdir/mask $outdir/native_space/sensitivity
elif [ ! -z $cref ]; then
    # Calculate sensitivty image using user-supplied cref image
    fslmaths $tempdir/calib -div $tempdir/cref -mas $tempdir/mask $outdir/native_space/sensitivity
fi

# Senstivity correction cannot be done if this image hasn't been generated by this point
if [ -z $outdir/native_space/sensitivity ]; then
    senscorr=""
    Warn "sensitivity correction has been requested, but suitable map is not available, skipping that step"
fi

# Defaults for (some) parameters
# deal with T1
if [ -z $t1set ]; then
    t1set=1.3;
fi
Log "T1: $t1set"

if [ -z $t1bset ]; then
# follws the ASL white paper recommendation
    t1bset=1.65;
fi
Log "T1b: $t1bset"


### Bolus duration(s)
if [ -z $boluset ]; then
    boluslen=1.8; # use the WP default
fi
Log "Bolus duration(s): $boluslen"

count=0
tauslist=""
thetaus=`echo $boluslen | sed 's:,: :g'`
for tau in $thetaus; do
    count=`expr ${count} + 1`
    tauslist=`echo $tauslist --tau${count}=$tau`
done

if [ $count -eq 1 ]; then
    tauslist="--tau=$tau" #single univerisal bolus duration
    Log "Bolus duration: $tau"
else
    Log "bolus duration list: $tauslist"
    if [ $count -ne $ntis ]; then
	Echo "Error: number bolus durations specified does not match the number of TIs - this is not possible for multiple bolus duration processing"
	exit 1
    fi
fi
### End of Bolus duration(s)

#pre-processing for epochwise analysis
# separate data into epochs here
if [ ! -z $epoch ]; then
if [ -z $eol ]; then
    eol=0
fi
    asl_file --data=$tempdir/diffdata --ntis=$ntis --ibf=tis --iaf=diff --epoch=$tempdir/epoch --elen=$elen --eol=$eol --eunit=tis
    eadv=`expr $elen - $eol`
fi


# write options file for BASIL - these are the core options that are appropraite whether we are doing a single or epochwise analysis
echo "Setting up BASIL"
Log "BASIL setup"

# T1 values
echo "--t1=$t1set --t1b=$t1bset" >> $tempdir/basil_options.txt

if [ ! -z $t1im ]; then
    basil_options=$basil_options"--t1im=$t1im "
    #echo "--t1im=$t1im" >> $tempdir/basil_options.txt
    Log "Using supplied T1 (tissue) image in BASIL: $t1im"
fi

# data acquired using CASL?
if [ ! -z $casl ]; then
    echo "--casl" >> $tempdir/basil_options.txt;
    Log "cASL model"
else
    Log "pASL model"
fi

#echo "--tau=$boluslen" >> $tempdir/basil_options.txt
echo $tauslist >> $tempdir/basil_options.txt


# slice timing correction?
if [ ! -z $slicedt ]; then
    echo "--slicedt=$slicedt" >> $tempdir/basil_options.txt
    Log "Slice timing correction with delta: $slicedt"
fi

# Flip anlge for look-locker readout
if [ ! -z $fa ]; then
    echo "--FA=$fa" >> $tempdir/basil_options.txt
    Log "Flip angle (look-locker readout): $fa"
fi

# Multi-band setup (if not set then this is ignored)
if [ ! -z $sliceband ]; then
    echo "--sliceband=$sliceband" >> $tempdir/basil_options.txt
    Log "Multi-band setup with number of slices per band: $slicedband"
fi

# Infer arterial component?
if [ -z $artoff ]; then
    basil_options=$basil_options"--inferart "
    Log "Infer arterial component"
fi
# fix the bolus duration?
if [ -z $fixbolus ]; then
    basil_options=$basil_options"--infertau "
    Log "Varaiable bolus duration"
else
    Log "Fixed bolus duration"
fi

#deal with BAT
if [ -z $bat ]; then
    if [ -z $casl ]; then
	bat=0.7 #PASL default
    else
	bat=1.3 #CASL default
    fi
fi
echo "--bat=$bat" >> $tempdir/basil_options.txt  

if [ -z $fixbat ]; then
    Log "Variable arterial arrival time"
    Log "Setting prior/initial (tissue/gray matter) bolus arrival time to $bat"

    # Tissue BAT SD
    #defaults
    if [ -z $singleti ]; then
	# multi TI/PLD data, set a more liberal prior for tissue ATT since we should be able to determine from data
	# NB this leave the arterial BAT alone.
	batsd=1;
    fi

    # if required add batsd option for basil
    if [ ! -z $batsd ]; then
	Log "Setting std dev of the (tissue) BAT prior to $batsd"
	echo "--batsd=$batsd" >> $tempdir/basil_options.txt
    fi
else
    basil_options=$basil_options"--fixbat " 
    Log "Fixed arterial arrival time"
    Log "Setting arterial arrival time to $bat"
fi

# Noise specification
if [ -z $snr ]; then
    snr=10; #default SNR
fi
if [ $tpoints -eq 1 ]; then
    # only a single time point in data, will use informative noise prior
   noiseprior=1
   Log "Single volume: informative noise prior will be used"
fi

if [ ! -z $noiseprior ]; then
    # use an informative nosie prior
     if [ -z $noisesd ]; then
	 Log "Using SNR of $snr to set noise std dev"
	# estimate signal magntiude
	fslmaths $tempdir/diffdata_mean -Tmax $tempdir/datamax
	brain_mag=`fslstats $tempdir/datamax -k $tempdir/mask -M`
	# this will correspond to whole brain CBF (roughly) - about 0.5 of GM
	noisesd=`echo "scale=2;sqrt( $brain_mag * 2 / $snr )" | bc`
    fi

    Log "Using a prior noise sd of: $noisesd"
    echo "--prior-noise-stddev=$noisesd" >> $tempdir/basil_options.txt
fi


# Exteneded options for BASIL
if [ ! -z $spatial ]; then
# if we are using spatial smoothing on CBF then we will also do the analysis in a single step
    echo "Instructing BASIL to use automated spatial smoothing"
    basil_options=$basil_options"--spatial "
    Log "Employing spatial VB"

fi

if [ ! -z $infert1 ]; then
    echo "Instructing BASIL to infer variable T1 values"
    basil_options=$basil_options"--infert1 "
    Log "Including T1 uncertainty"
fi


if [ ! -z $exch ]; then
    # use a specific exchange model in BASIL
    Log "Using exchange model: $exch"
    basil_options=$basil_options"--exch=$exch "
fi

if [ ! -z $disp ]; then
    # use a specific dispersion model in BASIL
    Log "Using dispersion model: $disp"
    basil_options=$basil_options"--disp=$disp "
fi

if [ ! -z $devel ]; then
    basil_options=$basil_options" --devel "
fi

if [ ! -z $model_options ]; then
    echo "Appending additional BASIL options to $tempdir/basil_options.txt"
    cat $model_options >> $tempdir/basil_options.txt
fi

Log "BASIL options ($tempdir/basil_options.txt):"
Log "----"
Log "`cat $tempdir/basil_options.txt`"
Log "----"
# -- end of main basil options setting

cp $tempdir/basil_options.txt $tempdir/basil_options_core.txt # keep a copy of the core options accumulated thus far (we might need these again for the epoch analysis)


##### Analyse data using BASIL
### First analysis on whole data, normal perfusion image
echo "Calling BASIL on data - conventional perusion image"
initbasil="" # Can be used to pass an intital MVN into the main run of BASIL from an intial run (below)
if [ $repeats -gt 1 ] || [ $repeats -eq 0 ]; then
    # do an initial analysis using the data averaged at each TI
    # NB repeats=0 is a special case of variable number of repeats at each TI
    Log "Initial run of BASIL on data where we have avareged all repeats at each TI"
    datafile=$tempdir/diffdata_mean
    mkdir $tempdir/init
    cat $tempdir/basil_options_core.txt > $tempdir/init/basil_options.txt
    echo "--repeats=1" >> $tempdir/init/basil_options.txt
    echo "$tislist" >> $tempdir/init/basil_options.txt
    Dobasil $datafile $tempdir/init
    initbasil=$tempdir/init/finalMVN
fi

# main analysis using full data
datafile=$tempdir/diffdata
if [ $repeats -gt 0 ]; then
    echo "--repeats=$repeats" >> $tempdir/basil_options.txt
else
    # variable number of repeats at each TI - tell basil
    echo "$rptslist" >> $tempdir/basil_options.txt
fi
echo "$tislist" >> $tempdir/basil_options.txt

Log "Main run of BASIL on ASL data"
Dobasil $datafile $tempdir $initbasil
### End of: First analysis on whole data

### Registration (2/2)
# Revisit the registration now that we have a pefusion image (with good GM/WM contrast) using BBR
# use existing registration for initial aligment
if [ $register -eq 1 ]; then
    if [ $finalreg -eq 1 ]; then
	echo "Performing final registration"
	Log "Final registration"
	cp $tempdir/asl2struct.mat $outdir/native_space/asl2struct_init.mat #preserve the intial registration for future reference
	Registration $tempdir/ftiss "-m $tempdir/mask --tissseg $tempdir/tissseg --imat $tempdir/asl2struct.mat --finalonly"
    fi
fi
### End of: Registration (2/2)

### Partial Volume Estimates
# Note we do this here since we have the final registration now which we need to transform PV estimates into ASL space
if [ ! -z $fasthasrun ] && [ -z $pvgm ]; then
    # PVE in ASL space from strcutural segmentation results
    # invert the transformation matrix
    convert_xfm -omat $tempdir/struct2asl.mat -inverse $tempdir/asl2struct.mat
    
    # Gray matter - assume this will be PVE 1
    applywarp --ref=$tempdir/asldata --in=$tempdir/pvgm_struct --out=$tempdir/pvgm_inasl --premat=$tempdir/struct2asl.mat --super --interp=spline --superlevel=4
    # white matter  - assume this will be PVE 2
    applywarp --ref=$tempdir/asldata --in=$tempdir/pvwm_struct --out=$tempdir/pvwm_inasl --premat=$tempdir/struct2asl.mat --super --interp=spline --superlevel=4
    # threshold (upper and lower) the PVE to avoid artefacts of spline interpolation and also ignore very low PVE that could cause numerical issues.
    fslmaths $tempdir/pvgm_inasl -thr 0.1 -min 1 $tempdir/pvgm_inasl
    fslmaths $tempdir/pvwm_inasl -thr 0.1 -min 1 $tempdir/pvwm_inasl
    pvexist=1
fi

if [ ! -z $pvgm ]; then
    #using supplied PV images
	Log "Loading supplied PV images"
	if [ -z $pvwm ]; then
	    echo "ERROR: no WM PV image has been supplied"
	fi
	Log "PV GM is: $pvgm"
	fslmaths $pvgm -thr 0.1 -min 1 $tempdir/pvgm_inasl
	Log "PV WM is: $pvwm"
	fslmaths $pvwm -thr 0.1 -min 1 $tempdir/pvwm_inasl
	pvexist=1
fi

if [ ! -z $pvexist ]; then
    # make some masks 
    # these are currently used for masking after model fitting
    fslmaths $tempdir/pvgm_inasl -thr 0.1 -bin $tempdir/gmmask
    fslmaths $tempdir/pvwm_inasl -thr 0.1 -bin $tempdir/wmmask
    # these are for calculating mean perfusion within tissue types
    fslmaths $tempdir/pvgm_inasl -thr 0.8 -bin $tempdir/gmmask_pure
    fslmaths $tempdir/pvwm_inasl -thr 0.9 -bin $tempdir/wmmask_pure
fi
### End of: Partial Volume Estimates

### Calibration
# Do calibration here becuase we do not need it before this point & if we are generating a CSF mask we have a better registration at this point
if [ -z $t1tset ]; then
    t1tset=1.3;
fi
Log "T1t (for calibration): $t1tset"

# TR (for calibration image)
if [ -z $tr ]; then
    tr=3.2
fi


# calibration image gain
if [ -z $cgain ]; then
    cgain=1;
fi

# Calibration if reqd
if [ -z $alpha ]; then
        # based on the ASL white paper
    if [ -z $casl ]; then
	alpha=0.98;
    else
	alpha=0.85;
    fi
fi

if [ -z $cmethod ]; then
# default calibration method is 'voxelwise' unless we have CSF PV estimates or CSF mask has been supplied
    if [ ! -z $fasthasrun ] || [ ! -z $csf ]; then
	cmethod=single
    else
	cmethod=voxel
    fi
fi

if [ ! -z $calib ]; then

    # Single M0 value for calibration
    if [ $cmethod = 'single' ]; then
	Log "Calibration is using a single M0 value with a CSF reference"
	if [ -z $csf ] && [ -z $fasthasrun ]; then
	    echo "ERROR: Provide either a structural image or CSF mask for calibration when using --cmethod=single"
	    exit 1
	fi
       # calcualte M0a from CSF
	Calibration
	Mo=`cat $outdir/calib/M0.txt`

    # Voxelwise M0 values for calibration
    elif [ $cmethod = 'voxel' ]; then
	Log "Calibration is voxelwise"
	mkdir $outdir/calib
        # copy over the calibration image and apply the cgain setting - this increases the magntiude of M0 to match that of the ASL data (acquired with a higher gain - cgain>=1 normally)
	fslmaths $calib -mul $cgain $outdir/calib/M0
	Mo=$outdir/calib/M0 
	if [ 1 -eq `echo "$tr < 5" | bc`  ]; then
	 # correct the M0 image for short TR using the equation from the white paper
	    Log "Correcting the calibration (M0) image for short TR (using T1 of tissue $t1tset)"
	    ccorr=`echo "1 / (1 - e(- $tr / $t1tset) )" | bc -l`
	    fslmaths $Mo -mul $ccorr $Mo
	fi

	#inlcude partiition co-effcient in M0 image to convert from M0 tissue to M0 arterial
	fslmaths $Mo -div 0.9 $Mo

	if [ ! -z $edgecorr ]; then
	    # correct for (partial volume) edge effects
	    # median smoothing and erosion
	    fslmaths $Mo -fmedian -mas $tempdir/mask -ero $tempdir/calib_ero
	    # extrapolation to match mask
	    asl_file --data=$tempdir/calib_ero --ntis=1 --mask=$tempdir/mask --extrapolate --neighbour=5 --out=$Mo
	fi
    else
	echo "Error unrecognised calibration method: $cmethod, (use single or voxel)"
    fi 
elif [ ! -z $M0 ]; then
    # An M0 value has been supplied, use this
    cmethod=single # we are in 'single' mode as a single value has been supplied
    Mo=$M0
    echo "M0: $Mo"
    Log "Using supplied M0 value: $Mo"
fi

### End of: Calibration


### Output main BASIL results
# Note we do this here, as we have the registration done and masks created and calibration complete
Dooutput

# save the mask used to the (native space) output directory
imcp $tempdir/mask $outdir/native_space/mask
### End of: Output main BASIL results

### Partial Volume Correction BASIL
if [ ! -z $pvcorr ]; then
    if [ -f $tempdir/struc_bet.* ]; then
	# redo the mask now that we have a better registration - as this might matter for PV correction
	# NB we dont use the PVE here since we dont (necessarily) want to exclude the ventricles from the mask as this has implications for the spatial priors
	fslmaths $tempdir/struc_bet -bin $tempdir/struc_bet_mask
	flirt -in $tempdir/struc_bet_mask -ref $regfrom -applyxfm -init $tempdir/struct2asl.mat -out $tempdir/mask -interp trilinear
	fslmaths $tempdir/mask -thr 0.25 -bin -fillh $tempdir/mask
	fslcpgeom $regfrom $tempdir/mask
	imcp $tempdir/mask $outdir/native_space/mask_pvcorr # copy new mask to output directory - indicate that it was used for PV correction analysis
    fi
    
    # intructions for BASIL
    basil_options=$basil_options" --pgm $tempdir/pvgm_inasl --pwm $tempdir/pvwm_inasl "
    mkdir $tempdir/pvcorr
    cp $tempdir/basil_options.txt $tempdir/pvcorr/basil_options.txt #Dobasil expects the options file to be in the subdirectory
    # Run BASIL
    Dobasil $datafile $tempdir/pvcorr

    imcp $tempdir/pvcorr/finalMVN $tempdir/finalMVN #just in case we are about to do a epochwise analysis

    #output the results
    Dooutput pvcorr
fi
### End of: Partial Volume Correction

### Epoch BASIL
if [ ! -z $epoch ]; then
    # epochwise analysis
    echo "Epochwise analysis"

    #genereate a list of epochs
    currdir=`pwd`
    cd $tempdir
    epochlist=`imglob epoch*`
    cd $currdir

    ecount=0
    for e in $epochlist; do
	Log "Processing epoch: $e"
	etislist=""
        # deal with the TIs
	for ((ei=0; ei<$elen; ei++)); do
	    ethis=`expr $ecount \* $eadv + $ei`
	    #echo $ethis
	    eidx=`expr $ei + 1`
	    #echo $ei
	    #echo ${alltis[$ethis]}
	    etislist=$etislist" --ti${eidx}=${alltis[$ethis]}"
	done
	Log "TIs for this epoch: "
	Log $etislist

	mkdir $tempdir/$e
	cp $tempdir/basil_options_core.txt $tempdir/$e/basil_options.txt # get the 'core' options and make a new basil_options file jsut for this TI
	echo "--repeats=1" >> $tempdir/$e/basil_options.txt #for epochs we specify all the TIs explicitly
	echo $etislist >>  $tempdir/$e/basil_options.txt #these are the basil options for this epoch

	fast=2 #we now switch BASIL to fast level '2' - this means it will only do analysis in a single step from here on in, but we will use our existing analysis for initialisation.
	
	Dobasil $tempdir/$e $tempdir/$e $tempdir/basil/finalMVN # init with results of first basil run

        #output 
	Log "Saving results from epoch: $e"
	Dooutput $e

	ecount=`expr $ecount + 1`
    done
fi
### End of: Epoch BASIL




#OUTPUTS
# Setup option outputs - anything that would be common to all epochs
# note that we now do directory creation right at the start
#if [ ! -z $nativeout ]; then
#fi
if [ ! -z $structout ]; then
    #cp $tempdir/asl2struct.mat $outdir/struct_space/asl2struct.mat
    cp $tempdir/asl2struct.mat $outdir/native_space/asl2struct.mat #also provide the transformation matrix for reference
fi
#if [ ! -z $advout ]; then
#fi

#if [ -z $epoch ]; then
# normal single analysis of data
#Dooutput

##if [ ! -z $epoch ]; then
# epochwise analysis
#    for e in $epochlist; do
#	Log "Saving results from epoch: $e"
#	Dooutput $e
 #   done
#fi




if [ ! -z $pvcorr ]; then
# copy PVE in ASL space to output directory
imcp $tempdir/pvgm_inasl $outdir/native_space/pvgm_inasl
imcp $tempdir/pvwm_inasl $outdir/native_space/pvwm_inasl
fi

if [ ! -z $pvexist ]; then
    # copy PV masks to output directory
    imcp $tempdir/gmmask $outdir/native_space/gm_mask
    imcp $tempdir/wmmask $outdir/native_space/wm_mask
    imcp $tempdir/gmmask_pure $outdir/native_space/gm_roi
    imcp $tempdir/wmmask_pure $outdir/native_space/wm_roi
fi

# clearup
if [ ! -z $debug ]; then
    mv $tempdir $outdir
else
    rm -r $tempdir
fi


echo "Output is $outdir/"
echo "OXFORD_ASL - done."