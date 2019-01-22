#!/usr/bin/perl
#
# mkrdns - Make Reverse DNS - Version 3.3
#
# By: Theo Van Dinter (felicity@mkrdns.org) (c) 1998-2002
# Revision Info: $Id: mkrdns,v 1.59 2002/12/05 21:19:28 felicity Stab $
#
# The goal of this script is to automatically generate new reverse IP
# mapping zone files for DNS/BIND.  It's been done before, but there
# always seems to be something which makes it not workable in my
# environment.  This script fixes that problem by adapting as necessary.
#
# Feel free to subscribe to the mkrdns mailing list.  Instructions are
# available from the mkrdns web page: http://www.mkrdns.org/ The list is
# available to discuss mkrdns-related topics (mkrdns, DNS, etc.) and is
# also used to announce new versions of mkrdns.
#
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#

use strict;
use Getopt::Long;
use POSIX qw(strftime);

# User Specified variables (commandline)
my ($debug)    = 0;      # display debugging information (user)
my ($help)     = 0;      # help screen (user)
my ($bootfile) = "";     # configuration file to use (user)
my ($ext)      = "";     # extension for output files (user)
my ($quiet)    = 0;      # show errors only, or warnings too?
my ($version)  = 0;      # show version information
my ($rootdir)  = "/";    # root directory for files

# Program needed variables
my ( $i, @domains, %networks, %maps, %serial, %mips, %hash, %netmap, @toskip );
my ( %zonetoskip, $nameddir, %numordate, %files, $toskip, $ignoreslaves );
my ($pversion)  = "3.3";
my ($whichhash) = undef;    # which hash function to use

# Get commandline parameters
$i = &GetOptions(
  "debug"       => \$debug,
  "help|h"      => \$help,
  "extension=s" => \$ext,
  "quiet"       => \$quiet,
  "version"     => \$version,
  "rootdir=s"   => \$rootdir,
  "hash=i"      => \$whichhash,
  "<>"          => sub { $bootfile = $_[0] },    # any "non-option" is
                                                 # config (boot) file
);

if ( $version || !$i || $help ) {
  print "
mkrdns v$pversion (c) 1998-2002
By: Theo Van Dinter (felicity\@mkrdns.org)

";

  print "Usage: $0 [options] [configuration file]

Options:
-debug\t\tTurn on debugging (warning, this prints a *LOT* of info)
-extension\tAppend given extension to output files
-help\t\tShow this help screen
-quiet\t\tTurn off warning messages (multiple A records -> IP, etc.)
-rootdir\tSpecify the root directory that named will run in (chroot)
-version\tShow the mkrdns version information

Configuration file is the full path to either named.boot or named.conf.
If not specified, mkrdns will search common locations for the files.

" unless ($version);
  exit 0;
}

warn "(warn) The --hash option is depricated, just using 32-bit CRC built-in.\n"
  if ( defined $whichhash );

if ( $ext =~ /^\./ ) {    # Remove the '.'s from the start of the extention ...
  $ext =~ s/^\.+//;
  warn "(warn) Extension started with '.' -- removed.  Extention now '$ext'.\n";
}

if ($debug) {
  print "Debugging turned on.\n", "Version     = $pversion\n",
'C. Revision = $Id: mkrdns,v 1.59 2002/12/05 21:19:28 felicity Stab $',
    "\n", "Help        = $help\n", "Quiet Mode  = $quiet\n",
    "Root Dir    = $rootdir\n";
  print "Extension   = $ext\n" if ($ext);
  print "Hash Func   = 32-bit checksum\n";
  print "\n";
}

$rootdir = &FixPath($rootdir);
if ( $rootdir !~ m#^/# || $rootdir =~ m#^/?\.\.(/|$)# ) {
  die qq{(fatal) Root directory ("$rootdir") is invalid.\n};
}

# If bootfile wasn't specified, try to find one in standard locations ...
unless ($bootfile) {
  my ($stdloc);
  my (@locs) = qw{	/etc /var/named /usr/named /usr/local/etc
    /usr/freeware/etc /etc/named /etc/bind };

  warn
"(warn) No configuration file specified.  Checking in standard locations ...\n";

  foreach $stdloc (@locs) {
    opendir( DIR, $stdloc ) || next;
    my (@files) = grep( /^named\.(boot|conf)$/, readdir(DIR) );
    closedir(DIR);

    print "(debug) Config files found in $stdloc: ", join ( ",", @files ), "\n"
      if ($debug);

    if ( $#files == -1 ) {    # named.boot and named.conf weren't found, exit.
      print
        qq{(debug) Neither named.boot nor named.conf were found in "$stdloc".\n}
        if ($debug);
    }
    elsif ( $#files == 0 ) {    # one file was found, use it.
      $bootfile = "$stdloc/$files[0]";
      warn "(info) $bootfile was found.\n";
    }
    else {    # more than one file was found, use the "best" one.
      $bootfile = "$stdloc/named.conf";
      warn "(info) Multiple configuration files were found, using $bootfile.\n";
    }

    last if ($bootfile);
  }

  die
"(die) Couldn't find either named.boot or named.conf in any standard location.  Exiting.\n"
    unless ($bootfile);
}

READCONF: {
  my ($type) =
    ( $bootfile =~ /\.(\w+)$/ );  # what kind of config file (boot, conf, etc.)?

  # neither boot nor conf -- start crying and exit.
  if ( $type !~ /^(boot|conf)$/ ) {
    die "(fatal) $bootfile is neither a boot nor conf file.\n";
  }

  # Read configuration file into memory.
  my ($config);
  open( CONF, "<$bootfile" ) || die "(fatal) Can't open $bootfile:$!";
  while ( $_ = <CONF> ) {         # deal with the includes!
    if ( ( /^directory/i && $type eq "boot" )
      || ( /\bdirectory\s+"[^"]+";/ && $type eq "conf" ) )
    {
      $nameddir = (m/\bdirectory\s+"?([^"\s]+)"?/i)[0];
      print "(debug) Named Directory = $nameddir\n" if ($debug);
    }

    if ( ( /^\s*include\s/i && $type eq "boot" )
      || ( /\binclude\s+"/i && $type eq "conf" ) )
    {                             # include statement!
      my (@conf) = ($_);

      # (boot) ^include <file>
      # (conf) ^include "<file>";
      for ( my ($i) = 0 ; $i <= $#conf ; $i++ ) {
        next
          unless ( $conf[$i] =~ /\binclude\s/i );    # skip non includes ...
        chomp $conf[$i];
        print "(debug) Include statement ($conf[$i]) found.\n"
          if ($debug);

        my ($file) = ( $conf[$i] =~ m/\binclude\s+"?([^"\s]+)"?/i );
        $file =~ s/\s+//;    # files shouldn't have whitespace ...
        unless ( $file =~ m!^/! ) {    # relative
          unless ($nameddir) {         # include before directory?  boo!
            $nameddir = ".";
            warn
qq{(warn) Include found before named directory was specified!  Using ".".\n};
          }
          $file = "$nameddir/$file";
        }

        $file = &Handle_Path( $rootdir, $file );
        print "(debug) Including file $file.\n" if ($debug);
        open( IN, "<$file" ) || die "(fatal) Can't open $file:$!";
        if ( $type eq "boot" ) {
          splice @conf, $i--, 1,
            <IN>;    # replace include with data then recheck index
        }
        elsif ( $type eq "conf" ) {
          $conf[$i] =~ /^(.*)\binclude\s+"?[^"\s]+"?\;(.*)$/i;
          splice @conf, $i--, 1, $1, <IN>, $2;
        }
        close(IN);
      }

      $config .= join ( "", @conf );    # tack in included stuff ...
      next;
    }

    $config .= $_;                      # append single line!
  }
  close(CONF);
  print "(debug) Read in $bootfile.\n" if ($debug);

  # no directory statement anywhere?
  die "(fatal) No named directory specified!\n" unless ($nameddir);

  if ( $type eq "boot" ) {              # parse named.boot
                                        # deal with directives
    foreach ( grep( /^;\s*mkrdns\s+/, split ( /\n/, $config ) ) ) {
      s/^;\s*mkrdns\s+//;
      &Directives($_);
    }

    foreach $i ( split ( /\n/, $config ) ) {
      $i =~ s/;.*$//;                   # remove comments
      $i =~ s/^\s+//;                   # remove whitespace
      $i =~ s/\s+$//;

      if ( $i =~ /^(primary|secondary)/i ) {    # primary/secondary domain ...
        my ( $type, $domain, $tmp, $file ) =
          ( $i =~ /^(\S+)\s+(\S+)\s+(\S+\s+)?(\S+)\s*$/ );

        &Handle_Domain( 'default', $type, $domain, $file, \%files );
      }
    }
  }
  elsif ( $type eq "conf" ) {                   # parse named.conf
    my ($directives) = ( $config =~ m!^/\*\s*mkrdns(.+?)\*/!msi );

    if ($directives) {                          # mkrdns directive
      foreach $i ( split ( /\n/, $directives ) ) {
        $i =~ s/\#.+$//;
        $i =~ s/^\s+//;
        $i =~ s/\s+$//;

        next unless $i =~ /\S/;

        &Directives($i);
      }
    }

    # Remove comments from config!
    $config =~ s!/\*.*?\*/!!gs;    # /* ... */
    $config =~ s!//.*?\n!\n!gs;    # // ...
    $config =~ s!\#.*?\n!\n!gs;    # # ...

    # determine which domains and networks we are master for.

    # Set the defaults
    my $count = 0;
    my $view  = "default";
    my $views = undef;
    my $zone  = undef;
    my $type  = undef;
    my $file  = undef;

    # some people have whitespace between } and ;, so fix it...
    $config =~ s/}\s+;/};/g;

    # The controls { inet ... }; thing is the only one that
    # doesn't have a }; at the end of one of the sections.
    # That's very annoying, so we get rid of it all since we don't
    # need it anyway.  The inet command is supposedly the only
    # thing valid in the controls section, but there can multiple
    # inet entries, so we remove them all.
    $config =~ s/\bcontrols\s*{(?:\s*inet\b.+?};)+\s*};//s;

    # Make sure that the { and }; are properly on their own.
    $config =~ s/};/\n};/g;
    $config =~ s/{/{\n/g;

    # Each config line should be by itself for easier parsing
    $config =~ s/\;/\;\n/g;

    # Go through the input file!
    foreach ( split ( /\n/, $config ) ) {
      if (/\bview\s+"([^"]+)"/i) {    # If we see a view statement ...
        $view = $1;                   # set the view

        # Now figure out if the statement is valid or not.
        if ( defined $views && $views == 0 ) {

          # A view was defined after a non-viewed zone ...

          die "Can't have non-zoned and zoned views!\n";
        }
        if ( $count > 0 ) {

          # A view must not be enclosed in bracies.

          die "Views must be defined at the top level (view $view).\n";
        }

        # We know that we're validly views now.
        $views = 1 unless defined $views;
      }
      elsif (/\bzone\s+"([^"]+)"/i) {    # Now we see a zone statement ...
        $zone = lc $1;                   # set the zone

        # Now figure out if the statement is valid or not.
        if ( defined $views && $views == 1 && $count < 1 ) {

          # A zone must either be in a view or at the top level

          die "Can't have non-zoned and zoned views!\n";
        }
        if ( $count > 1 ) {
          die "Zones are not embedable (zone $zone is in another zone)!\n";
        }

        # If we're a zone and not in a view ...
        # $views == $count so that we can verify the level we should
        # be at for config options.
        $views = $count unless defined $views;
      }

      # Re-calculate our config level
      $count += /{/g;
      $count -= /};/g;

      # If there's a configuration file error and too many }; are found ...
      die "Too many }; found!\n" if ( $count < 0 );

      # Reset things if we've closed all our config levels out ...
      $view = "default" if ( $count < 1 );
      if ( !defined $views || $count <= $views ) {
        if ( defined $zone && defined $type && !defined $file ) {
          warn qq{(warn) No file specified for zone "$zone" in "$bootfile".\n};
        }

        $zone = undef;
        $type = undef;
        $file = undef;
      }

      next unless ( defined $zone );    # we need to be in a zone
      next if ( $count != $views + 1 ); # we need to be at the right level
      next unless /\b(type|file)\b/i;   # only use type and file

      if (/\btype\s+(master|slave)\b/i) {
        $type = lc $1;
      }
      if (/\bfile\s+"([^"]+)"/i) {
        $file = $1;
      }

      next unless ( defined $type && defined $file );

      Handle_Domain( $view, $type, $zone, $file, \%files );
    }

  }
}

# Take the array of regexps to skip and put them in a single var
$toskip = @toskip ? join ( "|", @toskip ) : undef;

# Read in current reverse maps, report errors.  Remember non-PTR lines
# for creation later on.
REVERSE: {
  while ( my ( $view, $nets ) = each %networks ) {
    while ( my ( $net, $file ) = each %{$nets} ) {
      open( IN, "<$file" )
        || die qq{(fatal) Can't open "$file" for reading:$!};
      seek( IN, 0, 0 );
      {
        local $/ = undef;    # slurp mode
        $hash{$file} = Do_Hash(<IN>); # get the hash value for the original file
      }

      print "(debug) Generated hash value for $file: $hash{$file}.\n"
        if ($debug);

      print "(debug) Scanning $file for non-PTR lines:\n" if ($debug);
      seek( IN, 0, 0 );

      # strip out PTR, $GENERATE, $ORIGIN, and $INCLUDE ...
      $maps{$view}->{$net} =
        join ( "", grep( !/(\s+PTR\s+|^\$(ORIGIN|INCLUDE|GENERATE))/i, <IN> ) );
      close(IN);

      # Pick out the serial number ( required to be the first RR,
      # so the regexp is not too complex. )
      ( $i = $maps{$view}->{$net} ) =~ s/\s*;.+?\n//g;    # remove comments
      ( $serial{$file} ) = ( $i =~ m!\s+SOA\s+\S+\s+\S+\s+(?:\(\s*)?(\d+)!is );

      if ($debug) {    # print out non-PTR records (long...?)
        foreach $i (
          split ( /\n/, $maps{$view}->{$net} ),
          "Parsed serial number: $serial{$file}"
          )
        {
          print "(debug) $i\n";
        }
      }
    }
  }
}

# Read in current forward maps, convert A records into PTR records,
# add to map.  If there are multiple A records for a given IP, report
# duplicate, and keep first.
#
# This routine is the biggest time suck...
#
READIN: {
  foreach (@domains) {
    my ( $view, $domain, $map ) =
      split ( /:/, $_ );    # $view = view, $domain = domain, $map = map file
    my ($last) = "$domain.";    # what to use in case of blank hostname
                                # hostname, $ORIGIN, domain in that order
    my ($end)  = $last;         # what to use in case of relative hostname
                                # $ORIGIN then domain, in that order

    print
      "(debug) Reading in entries from $map for domain $domain, view $view.\n"
      if ($debug);

    my (@data);
    open( IN, "<$map" ) || die "(fatal) Can't open $map:$!";
    chomp( @data = <IN> );      # slurp in map file w/out ending \n's
    close(IN);

    # deal with $INCLUDE and $GENERATE statements ...
    print "(debug) Scanning for \$INCLUDE and \$GENERATE statements...\n"
      if ($debug);

    for ( $i = 0 ; $i <= $#data ; $i++ ) {
      next
        unless ( $data[$i] =~ /^\$(INCLUDE|GENERATE)/ )
        ;                       # skip non-include/generate lines

      $data[$i] =~ s/;.*$//;    # remove comments & whitespace
      $data[$i] =~ s/\s+$//;

      if ( $data[$i] =~ /^\$GENERATE/ ) {
        print qq{(debug) "$data[$i]" specified.\n} if ($debug);

        # Set ORIGIN to blank -- we'll handle it later.
        splice @data, $i, 1, &Handle_GENERATE( "", $data[$i] );
      }
      elsif ( $data[$i] =~ /^\$INCLUDE/ ) {

        # $INCLUDE <file> <origin>
        my ( $inc, $file, $origin ) = split ( /\s+/, $data[$i] );

        print qq{(debug) "$data[$i]" specified.\n} if ($debug);

        $file = "$nameddir/$file" unless ( $file =~ m!^/! );

        $file = &Handle_Path( $rootdir, $file );
        my (@inc);
        open( IN, "<$file" )
          || die qq{(fatal) Can't read \$INCLUDE file "$file":$!};
        chomp( @inc = <IN> );
        close(IN);

        if ($origin) {    # specified origin applies only to specified
                          # include file.  put appropriate sections at end
                          # of zone file.  see BIND 3rd ed. p.146

          # put $ORIGIN and included file at the end of the config
          push ( @data, "\$ORIGIN $origin", @inc );
          splice @data, $i, 1;    # remove $INCLUDE line
        }
        else {    # just replace the $INCLUDE line with the contents of file
          splice @data, $i, 1, @inc;
        }
        $i--;     # rescan the line where the $INCLUDE was.
      }
    }

    # the file should be fully expanded in memory now.
    # go through all 'host ? ? ?' and $ORIGIN lines ...
    foreach $i ( grep( /^(\S*(\s+\d+)?(\s+\w+)?\s+\S+\s+|\$ORIGIN)/i, @data ) )
    {
      $i =~ s/\s*;.*$//;    # strip comments ...
      next unless ( length $i );    # skip blanks

      if ( $i =~ /^\$ORIGIN/i ) {   # $ORIGIN!
        $end = ( split ( /\s+/, $i ) )[1];
        $end .= ".$domain." if ( $end !~ /\.$/ );    # not FQDN

        $last = lc $end;
        print qq{(debug) "$i" specified.  Final = "$last".\n}
          if ($debug);

        next;
      }

      # parse the line
      # HOST TTL CLASS TYPE VALUE
      # TTL can be a number (seconds), or string
      #  (1w1d1h1m1s), max of 63 chars. lib/dns/ttl.c,
      #  function bind_ttl, BIND9.1.3.
      # According to RFC1035, class and ttl can be
      #  reversed. <grrr>
      #
      my ( $host, $type, $ip ) =
        ( $i =~
m!^(\S*)(?:\s+(?:\d+|(?:\d+[wdhms])+|IN|CS|CH|HS)){0,2}\s+(\w+)\s+(\S+)!i
        );

      $host = lc $host;    # lowercase the host
      $type = uc $type;    # make sure the type (A,MX,etc) is uppercase

      next unless ($type); # in SOA " 30 ; comment" ...

      $host = $end if ( $host eq "@" );    # @ = ORIGIN

      # what to do with host?  interact with last if necessary ...
      if ( $host eq "" ) {    # it's a blank, use the last entry ...
        $host = $last;
      }
      elsif ( $host !~ /\.$/ ) {    # relative hostname
        $last = $host = "$host.$end";
      }
      else {                        # FQDN!
        $last = $host;
      }

      # This needs to stay here for proper " A 10.0.0.0"
      # behavior -- DON'T MOVE ME (again) BAD BAD THEO!
      next unless ( $type eq "A" );    # skip non-A records

      # should we skip?
      if ( defined $toskip
        && ( $host =~ /$toskip/o || $ip =~ /$toskip/o ) )
      {
        print "(debug) Skipping $host/$ip, matched toskip regexp ($toskip).\n"
          if ($debug);
        next;
      }

      # do network mapping
      if ( keys %netmap ) {
        my ($ipm) = &GenMask($ip);
        foreach $i ( keys %netmap ) {
          my ( $newnet, $netm, $mask ) = @{ $netmap{$i} };

          unless ( ( $ipm ^ $netm ) & $mask ) {    # 0 if in match made
            my ($ptr) = ( $ip =~ /\.(\d+)$/ );
            print "(debug) $ip mapping to $newnet.$ptr ...\n"
              if ($debug);
            $ip = "$newnet.$ptr";
            last;    # IPs should only match once ...
          }
        }
      }

      # figure out which network this IP is in ...
      my ($network) = &IPinNetwork( $ip, $view, \%networks );
      unless ( defined $network ) {
        print "(debug) Not keeping $host = $ip, not in any network.\n"
          if ($debug);
        next;
      }

      # the original may or may not be all numeric (maps)
      my ( $orig, $ptr ) = ( $ip =~ /^(.+)\.(\d+)$/ );
      if ( exists( $mips{$view}->{$network}->{$orig}->{$ptr} ) )
      {    # IP already has mapping!
        print qq{The entry in "$map" for "$host" duplicated "},
          $mips{$view}->{$network}->{$orig}->{$ptr},
          qq{".\nKeeping the original entry.\n}
          unless ($quiet);
        print
          "(debug) Not keeping $host = $ip, a PTR has already been defined ("
          . $mips{$view}->{$network}->{$orig}->{$ptr} . ").\n"
          if ($debug);
        next;
      }

      print "(debug) Keeping $host = $ip, in network $network, view $view.\n"
        if ($debug);

      # Network/origin/ptr = host
      $mips{$view}->{$network}->{$orig}->{$ptr} = $host;
    }
  }
}

# Check each output zone file to see if it needs changing
HASH: {
  while ( my ( $view, $nets ) = each %networks ) {
    print "(debug) Checking view $view for file changes ...\n" if ($debug);

    while ( my ( $net, $file ) = each %{$nets} ) {
      my ( $orig, $ptr );
      my ($map) = $maps{$view}->{$net};

      %{ $mips{$view}->{$net} } = ()
        unless ( defined $mips{$view}->{$net} );    # no IPs in net!
           # Stole this from http://www.sysarch.com/perl/sort_paper.html ;)
      foreach $orig (
        sort {
          pack( 'C*'   => split ( /\./, $a ) ) cmp
            pack( 'C*' => split ( /\./, $b ) )

        } keys %{ $mips{$view}->{$net} }
        )
      {
        $map .= "\$ORIGIN "
          . join ( ".", reverse( split ( /\./, $orig ) ) )
          . ".in-addr.arpa.\n";    # append $ORIGIN to map
        my $ptrs = $mips{$view}->{$net}->{$orig};
        foreach $ptr ( sort { $a <=> $b } keys %{$ptrs} ) {

          # Add PTR line to map
          $map .= "$ptr\tPTR\t" . $ptrs->{$ptr} . "\n";
        }

      }

      my ($hv) = Do_Hash($map);    # generate hash value for new map
      print
        "(debug) Generated hash values for $file (old/new): $hash{$file}/$hv.\n"
        if ($debug);

      if ( $hv ne $hash{$file} ) {    # maps are different!
        print "(debug) File $file needs to be updated.\n" if ($debug);

        my ($fserial);
        my ($use) = $numordate{ $files{$file} }
          || "number";

        print "(debug) File $file uses serial type $use.\n" if ($debug);

        if ( $use eq "date" ) {
          $fserial = &strftime( "%Y%m%d00", localtime(time) );

          # if fserial > serial, then use fserial directly ...
          if ( $fserial <= $serial{$file} )
          {    # serial is >= fserial, add 1 to serial and use it if possible

            if ( $serial{$file} =~ /99$/ ) {    # version 99! can't roll.
              die
qq#(fatal) Serial number $serial{$file} (file "$file") ends in 99 -- can't add 1!  Freaky!\n#;
            }

            $fserial = $serial{$file} + 1;
          }
        }
        elsif ( $use eq "number" ) {
          $fserial = $serial{$file} + 1;
        }
        else {
          die qq{(fatal) Unknown serial type "$use".};
        }

        warn "(warn) Serial number for $file is at max.\n"
          if ( $fserial > 4294967294 );

        print "(debug) Changing serial number for $file from",
          " $serial{$file} to $fserial\n"
          if ($debug);

        $map =~ s/(\s+SOA\s+\S+\s+\S+\s+(?:\(\s*)?)$serial{$file}/$1$fserial/s;

        $file .= ".$ext" if ($ext);    # file or file.ext?

        print qq{Updating file "$file"\n} unless ($quiet);
        open( OUT, ">$file" )
          || die "(fatal) Can't open $file for writing:$!";
        print OUT $map;
        close(OUT);
      }
      else {
        print "File $file needs no modification.\n" unless ($quiet);
      }
    }
  }
}

exit 0;

# Is the given IP address in any of the specified networks?
# note: this routine only checks on byte boundaries
# Return undef if not, network number if yes.
#
{
  my %cache = ();

  sub IPinNetwork {
    my ( $ip, $view, $networks ) = @_;  # IP to check, hash of networks to check

    my ($orig) = ( $ip =~ /^(.+)\.\d+$/ );
    return $cache{$view}->{$orig} if exists $cache{$view}->{$orig};

    do {    # matches most specific network first (10.0.49 before 10 ...)
      $ip =~ s/\.[^\.]+$//;    # remove last octet (host #)
      if ( exists $networks->{$view}->{$ip} ) {
        $cache{$view}->{$orig} = $ip;
        return $ip;
      }
    } while ( $ip =~ /\./ );    # while there's a period in the IP

    return undef;
  }
}

# Generate a bitmask from an IP/Network/bit count.
# Returns array of bitmasks from array of input values.
#
sub GenMask {
  if ( $_[0] =~ /^\d+$/ ) {     # /27 ...
    return ~( 2**( 32 - $_[0] ) - 1 );
  }
  else {                        # 255.255.255.224 ...
    return unpack( "N", pack( 'C4' => split ( /\./, $_[0] ) ) );
  }
}

# Parse the directive statements and plop the info in the right place.
#
sub Directives {
  my ( $type, $vals ) = split ( /\s+/, $_[0], 2 );
  print qq{(debug) mkrdns directive, type "$type", vals "$vals"\n}
    if ($debug);

  $type = lc $type;
  if ( $type eq "map" ) {
    my ( $nm, $nn ) = split ( /\s+/, $vals );
    @{ $netmap{$nm} } = ( $nn, map { &GenMask($_) } split ( /\//, $nm ) );
  }
  elsif ( $type eq "skip" ) {
    push ( @toskip, $vals );
  }
  elsif ( $type eq "skipzone" ) {
    map {
      my ( $v, $d ) = split ( /:/, $_, 2 );
      ( $v, $d ) = ( "default", $v ) if ( !defined $d );
      $zonetoskip{ lc $v }->{ lc $d } = 1;
    } split ( /\s+/, $vals );
  }
  elsif ( $type eq "serialt" ) {

    # $vals = "default|zone number|date"
    $vals = lc $vals;
    my ( $view, $zone, $nord ) = split ( /\s+/, $vals, 3 );
    ( $view, $zone, $nord ) = ( 'default', $view, $zone )
      if ( !defined $nord );    # backwards compatibility

    die qq{(fatal) mkrdns directive "$type $vals" invalid.}
      if ( $nord !~ /^(number|date)$/ );

    $numordate{"$view:$zone"} = $nord;
  }
  elsif ( $type eq "ignoreslaves" ) {
    $ignoreslaves = 1;
  }
  else {
    die qq{(fatal) mkrdns directive type "$type" is unknown.};
  }
}

# Generate actual lines from $GENERATE statements
# This routine should actually handle all $GENERATE types, although we're
# only going to use it for A records in mkrdns ...
#
sub Handle_GENERATE {
  my ( $ORIGIN, $GENERATE ) = @_;
  my (@toreturn) = ();

  # $RANGE is 'start-stop[/step]', all must be positive
  # $LHS/$RHS:
  #	$ is replaced by iterator value.
  #	\$ is a $ at the end.
  #	$\{ is replaced by the iterator value and the actual { char.
  #	Append $ORIGIN if $RHS!~/\.$/
  #	${offset} where offset defaults to "0,1,d".
  #		offset (integer),min width (0 padded),radix (doxX)
  # $TYPE is A|AAAA|PTR|CNAME|NS

  my ( $RANGE, $LHS, $TYPE, $RHS ) = ( split ( /\s+/, $GENERATE ) )[ 1 .. 4 ];
  die qq{(fatal) Invalid \$GENERATE line: "$GENERATE"\n}
    unless ( defined($RANGE)
    && defined($LHS)
    && defined($TYPE)
    && defined($RHS) );

  $TYPE = uc $TYPE;
  die qq{(fatal) Invalid \$GENERATE line (bad type): "$GENERATE"\n}
    unless ( $TYPE =~ /^(A|AAAA|PTR|CNAME|NS)$/ );

  my ( $START, $STOP, $SKIP ) = ( $RANGE =~ m{^(\d+)-(\d+)(?:/(\d+))?$} );
  if ( !defined($SKIP) || ( defined($SKIP) && $SKIP < 1 ) ) {
    warn qq{(warn) Invalid \$GENERATE line (bad skip): "$GENERATE" (set to 1)\n}
      if ( defined $SKIP );
    $SKIP = 1;    # skip defaults to 1 if not specified.
  }

  die qq{(fatal) Invalid \$GENERATE line (non-pos value): "$GENERATE"\n}
    unless ( $START > 0 && $STOP > 0 );

  # Convert trouble-some combinations out of the way.
  foreach ( $LHS, $RHS ) {
    s/\$\\\{/\$\377/g;    # $\{ -> $\377

    # Literal $'s in the statement
    s/\\\$/\376/g;        # \$  -> \376
    s/\$\$/\376/g;        # $$  -> \376

    # Replace $ or ${...} w/ valid ${offset,width,radix} sections.
    s@\$(?:{([^}]+)})?@
			my($o,$w,$r) = split(/,/,(defined $1?$1:""));
	
			# Want to set to the default if not defined or invalid,
			# only want to warn if invalid.
			if ( !defined($o) || $o!~/^-?\d+$/ ) {
				warn qq{(warn) Invalid \$GENERATE line (bad offset): "$GENERATE" (set to 0)\n}
					if ( defined($o) );
				
				$o = 0;
			}
	
			if ( !defined($w) || $w<1 ) {
				warn qq{(warn) Invalid \$GENERATE line (bad width): "$GENERATE" (set to 1)\n}
					if ( defined($w) );
				
				$w = 1;
			}
	
			if ( !defined($r) || $r !~ /^[doxX]$/ ) {
				warn qq{(warn) Invalid \$GENERATE line (bad radix): "$GENERATE" (set to d)\n}
					if ( defined($r) );
				
				$r = "d";
			}
	
			"\${$o,$w,$r}";
		@ge;
  }

  for ( my ($IT) = $START ; $IT <= $STOP ; $IT += $SKIP ) {
    $_ = "$LHS $RHS";

    # The only $'s left in the string should be iterator values.
    s@\${([^}]+)}@
			my($o,$w,$r) = split(/,/,$1);
			sprintf "%0$w$r", $IT+$o;
		@ge;

    tr/\377\376/{$/;    # Put the chars back in as literals.

    my ( $l, $r ) = split;

    if ( $ORIGIN ne "" ) {

      # The right side of an A or AAAA record is an address...
      foreach ( ( $TYPE =~ /^A/ ) ? $l : ( $l, $r ) ) {
        $_ .= ".$ORIGIN" unless (/\.$/);
      }
    }

    push ( @toreturn, "$l $TYPE $r" );
  }

  return @toreturn;
}

# This section of code takes in a line from the named configuration file and
# puts the info in the appropriate spots.  This used to be in both the
# named.conf and named.boot handlers in the main set of code, but the code
# was exactly the same, so I put it here for maintainability.
#
sub Handle_Domain {
  my ( $view, $type, $domain, $file, $files ) = @_;
  $domain = lc $domain;

  if ( $zonetoskip{$view}->{$domain} ) {
    print "(debug) Skipping view $view, zone $domain, matched skipzone.\n"
      if ($debug);
    return;
  }

  unless ( $domain && $file ) {
    warn
qq{(warn) No file specified for view "$view", zone "$domain" in "$bootfile".\n};
    return;
  }

  if ( $type =~ /^(slave|secondary)$/i && defined($ignoreslaves) ) {
    print "(debug) Skipping slave $view:$domain\n" if ($debug);
    return;
  }

  $file = "$nameddir/$file" if ( $file !~ m!^/! );
  $file = &Handle_Path( $rootdir, $file );

  if ( $domain =~ /\.arpa$/i ) {    # network
                                    # The file is already being used!
    die
qq#(fatal) The zone file "$file" is being used by two zones!  Error in config file!\n($files->{$file} and $view:$domain ...)\n#
      if ( exists $files->{$file} );

    $files->{$file} = "$view:$domain";

    if ( $type =~ /^(secondary|slave)$/i ) {
      print "(debug) Skipping slave reverse zone $view:$domain\n"
        if ($debug);
      return;
    }

    $domain =~ s/\.in-addr\.arpa$//i;    # just the net ...
    if ( $domain =~ /127$/ ) {           # silently skip 127.*
      print "(debug) Skipping $file for the 127.* network.\n"
        if ($debug);
      return;
    }
    $domain = join ( ".", reverse( split ( /\./, $domain ) ) );
    $networks{$view}->{$domain} = $file;
    print
      qq{(debug) Network "$domain", View "$view", File "$file", Type "$type".\n}
      if ($debug);
  }
  else {    # "normal" domain, read in domains in order presented.
    push ( @domains, "$view:$domain:$file" );
    print
      qq{(debug) Domain "$domain", View "$view", File "$file", Type "$type".\n}
      if ($debug);
  }
}

# Trim down a path to a standardized form.
# ie: /path/../foo -> /foo
#
sub FixPath {
  $_ = $_[0];

  tr#/#/#s;                  # Remove multiple /'s
  s#/\./#/#g;                # /./ -> /
  s#/\.$##;                  # remove /.$
  s#(^|/)[^/]*/\.\./#/#g;    # /[^/]/../ -> /
  s#(^|/)[^/]*/\.\.$##g;     # remove /..$
  s#^\./##;                  # remove ^./

  return $_;
}

# Take a given path, handle a possibly different root directory, then return
# it.
#
sub Handle_Path {
  my ( $rootdir, $orig ) = @_;

  my ($new) = &FixPath($orig);

  if ( $new =~ m#^/?\.\.(/|$)# ) {
    warn
qq{(warn) Path "$_" tries to go beyond root directory ("$new").  Removing.\n}
      unless ($quiet);
    $new =~ s#^/?\.\.(/|$)##;
  }

  $new = &FixPath("$rootdir/$new");
  if ( $orig ne $new ) {
    print qq{(debug) Path changed from "$orig" to "$new".\n} if ($debug);
    $orig = $new;
  }

  return $orig;
}

sub Do_Hash {
  # Built-in (32bit checksum)
  return unpack( "%32C*", $_[0] ) % 65535;   # generate 32-bit checksum for text
}

__END__

=head1 NAME

mkrdns - MaKe Reverse DNS (auto generate PTR maps)

=head1 SYNOPSIS

mkrdns [options] [configuration file]

=head1 DESCRIPTION

mkrdns is a program designed to auto-generate reverse DNS maps (IN PTR
records).  Some programs already accompany the BIND source package
that will do this kind of thing on a single domain or network basis.
mkrdns will read either a named.boot or named.conf file, figure out
which domains and networks to deal with, and then generate the reverse
maps.

You are deemed "in charge" of a network/domain if you are the primary
DNS for a reverse zone, or if you are either the primary or secondary
for a forward zone.  The exception to this rule is that the 127.*
network is not auto-generated due to the "1 IN PTR localhost." issue.

=head1 OPTIONS

-debug           Print debugging information.  (this will
                 print a B<LOT> of information, be warned.)

-extension <ext> Append the given extension to the output
                 files.  This is useful if you want to
                 have the reverse maps generated, but want
                 to check their contents before use.

-help            The help screen.

-quiet           Turn off warning messages (multiple A
                 records -> IP, etc.)  Good for scripts,
                 but you probably want to check on what
                 the warnings report. 

-rootdir <path>  Specify the path to the root directory
                 that named will be running in.  This
                 will handle anyone using a chrooted
                 environment for named.  Everything except
                 the configuration file is assumed to be
                 under the new root.

-version         Show mkrdns version information.

=head1 CONFIGURATION FILE

mkrdns reads the standard BIND configuration files I<named.boot> and
I<named.conf>.  If you don't specify the full path to the file on the
command line, mkrdns assumes that one (or both) will exist in /etc and
will search for them.  If none are found, the program exits.  If one
is found, it is used.  If both are found, named.conf is used.

=head1 DIRECTIVES

Think of directives as configuration options for mkrdns which are simply
comments to BIND.  The current directives are B<map>, B<serialt>, B<skip>,
and B<skipzone>.

B<Map> allows you to map hosts to another network.  This was designed in
for the purpose of handling DNS for a subnet of a class C network which
you do not control.  (See the DNS & BIND O'Reilly and Associates book,
3rd Ed., pg. 215-218) Assume that you have 10.4.4.32/27 (ie: you have
the 32 IPs from 10.4.4.32 to 10.4.4.63 ...)  You want to do reverse
mappings for those IPs, but you don't control 4.4.10.in-addr.arpa.
How do you do it?  The solution is to become the master for another
zone (such as 32.4.4.10.in-addr.arpa. or 32-63.4.4.10.in-addr.arpa.),
and CNAME the correct reverse pointers to the ones you're in charge of.
The format for the directive is:
   map <network/mask> <new network>

Ex: map 10.4.4.32/27 10.4.4.32-63

This maps all hosts between 10.4.4.32 and 10.4.4.63 to 10.4.4.32-63.32
to 10.4.4.32-63.63.

B<Serialt> will change mkrdns's behavior with the serial number for
certain zones.	By default, the serial number is assumed to be in I<date>
format (YYYYMMDDVV, year/month/day/version).  However, you can tell mkrdns
to treat the serial number as a regular number instead.  This allows
for more than 100 zone changes a day, and has a bit more flexibility
depending on the environment.  The format for the directive is:
	serialt <view> <zone> <format>

<view> specifies which view should be used for the behavior change.
If not specified, mkrdns assumes "default".  <zone> is either "default"
or the actual zone (ie: 0.0.0.10.in-addr.arpa).  <format> is either
"date" or "number".

Ex: serialt internal 1.168.192.in-addr.arpa number

B<Skip> forces mkrdns to ignore certain hosts/IPs via regular
expression. The concept is that there are some IN A records that
you would like to skip and not create a reverse entry.  Skip allows
this. (for instance, "foo IN A 10.4.4.32" and "mail IN A 10.4.4.32" both
exist, but you want to force foo as the reverse lookup and ignore mail.
The following example can do this for you.)  Format:
   skip <regular expression>

Ex: skip ^mail

This will skip any host (or IP) that matches the "^mail" regular
expression.  The host is the FQDN, and the IP is before mapping (see
above).

B<Skipzone> forces mkrdns to ignore certain zones while processing the
named configuration file.  A possible use for this is where you have
"bar.com" and "bar.net", and both of them should have the same host info
(ie: foo.bar.com and foo.bar.net both have the same records.)  You want
"bar.com" to be the reverse lookup for the IPs used.  So set the zone file
setting to the same file (bar.zone), and then add "skipzone bar.net".
B<NOTE:>  The skipzone argument must match EXACTLY with the zone name
in the config file.  B<NOTE:> You can specify multiple zones in the same
"skipzone" statement. (ie: "skipzone foo.com bar.com")  B<NOTE2:> If you are
using views, the zone string must be in the format "view:zone".  If a view
isn't given, "default" is assumed.

B<ignoreslaves> tells mkrdns to ignore any forward slave domains in
the configuration.  This is useful if, for instance, you are master for
both a forward domain and reverse domain (say 168.192.in-addr.arpa)
which go together, but you also have slave domains with hosts in the
same reverse zone.


The format of a directive differs (sorry) between named.conf and
named.boot.  UNIX-style comments (the hash mark then the comment) are
allowed.

=head2 named.boot directives

Directives look like a comment, so the format is simply:

 ; mkrdns <directive type> <parameters>

=head2 named.conf directives

To make directives more efficient with BIND 8, the format is slightly
different: 

 /* mkrdns
    <directive type> <parameters>
    ...
 */

=head1 EXAMPLES

B<mkrdns -e new /etc/named.boot>

This will run mkrdns over the file /etc/named.boot.  Output files will
be generated as <name>.new (i.e.: if the PTR zone file is called
160.zone, the output will be 160.zone.new.)

=head1 NOTES

I tend to use this script like a lint check.  i.e.: Edit the proper
zone files, then run mkrdns.

As with most documentation, there are probably things that aren't mentioned
in the docs that the script does/assumes/etc.  I apologize for any
inaccuracies/omissions.  Let me know if there are any parts that have an
"issue", and I'll see if I can't straighten it out.

=head1 ASSUMPTIONS

The <network>.zone reverse map files must already be created, be
uniquely specified in the configuration file, and have the appropriate
information (SOA/NS records, etc.) in there.  This script will strip
out any PTR records, and then add them back in.  (This means anything
like blank lines and comments will be moved to the top of the file.)
$ORIGIN and $INCLUDE are striped as of mkrdns 1.3.

You must be at least a secondary for all domains which reference IP
networks for which you're responsible.  There is no means (currently
at least) to specify a PTR record for a non-existent A record, so this
script must have access to all A records that need to be "reversed".

If you have more than 1 A record pointing to a specific IP, you can't
have both be the PTR record.  This script takes the first A record it
sees as the one used for the PTR record.  A warning is printed for any
additional entries.  (While the RFCs don't prohibit multiple PTR records
for the same IP, I have yet to find anyone who can give me a good reason
to do it.)

Map serial numbers default to be in YYYYMMDDVV format.  (YYYY = year,
MM = month, DD = day, VV = version (00-99).  This script will convert
your serial number to this format if it's not already.  I don't have too
many daily DNS changes, so the action for not being able to update the
serial number (ie: VV is at 99 and can't be increased) is to simply exit.
If this is going to cause a problem for you, you can use the serialt
directive to specify a zone (or the default) should treat the serial
number as a number instead of using the date format.  Either way,
a problem will come up when the serial number reaches 4294967295 (max
value), but that's another story.  (mkrdns will print a warning if this
is about to happen)

=head1 AUTHOR

Theo Van Dinter <felicity@mkrdns.org>

=cut
