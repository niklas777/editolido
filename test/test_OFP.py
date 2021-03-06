# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from unittest import TestCase
import mock
import os

from editolido.ofp import OFP
from editolido.route import Route
from editolido.geopoint import GeoPoint, dm_normalizer

DATADIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# noinspection PyUnresolvedReferences
patch_object = mock.patch.object


class TestOFP(TestCase):
    def test_get_between(self):
        with open(DATADIR + '/KJFK-LFPG 27Mar2015 05:45z OFP.txt', 'r') as f:
            ofp = OFP(f.read())

        s = ofp.get_between('WPT COORDINATES', '----')
        self.assertEqual(s[:4], 'KJFK')
        self.assertEqual(s[-21:-17], 'LFPG')

        s = ofp.get_between('WPT COORDINATES', '----', inclusive=True)
        self.assertTrue(s.startswith('WPT COORDINATES'))
        self.assertTrue(s.endswith('----'))
        self.assertEqual(s[15:19], 'KJFK')
        self.assertEqual(s[-25:-21], 'LFPG')

        with self.assertRaises(LookupError):
            ofp.get_between('####', '----')

        with self.assertRaises(EOFError):
            ofp.get_between('WPT COORDINATES', '****', end_is_optional=False)

        s = ofp.get_between('WPT COORDINATES', '****')
        self.assertTrue(s.endswith('STANDARD\n'))

        s = ofp.get_between('WPT COORDINATES', '****', inclusive=True)
        self.assertTrue(s.endswith('****'))

        s = ofp.get_between(None, 'KJFK/LFPG')
        self.assertEqual(s, 'retrieved: 27Mar/0429zAF  009  ')

        s = ofp.get_between('USED AS A ', None)
        self.assertEqual(s, 'STANDARD\n')

        s = ofp.get_between(None, None)
        self.assertEqual(s, ofp.text)

    def test_wpt_coordinates(self):
        with open(DATADIR + '/KJFK-LFPG 27Mar2015 05:45z OFP.txt', 'r') as f:
            ofp = OFP(f.read())
        points = list(ofp.wpt_coordinates())
        self.assertEqual(len(points), 31)
        self.assertEqual(points[0].name, 'KJFK')
        self.assertEqual(points[-1].name, 'LFPG')
        self.assertEqual(points[5].name, '')
        self.assertEqual(
            points[0],
            GeoPoint('N4038.4W07346.7', normalizer=dm_normalizer))
        self.assertEqual(
            points[-1],
            GeoPoint('N4900.6E00232.9', normalizer=dm_normalizer))
        self.assertEqual(
            points[5],
            GeoPoint('N5100.0W05000.0', normalizer=dm_normalizer))

    def test_wpt_coordinates_alternate(self):
        with open(DATADIR + '/KJFK-LFPG 27Mar2015 05:45z OFP.txt', 'r') as f:
            ofp = OFP(f.read())
            points = list(ofp.wpt_coordinates_alternate())
            self.assertEqual(
                points[0],
                GeoPoint('N4900.6E00232.9', normalizer=dm_normalizer))
            self.assertEqual(
                points[1],
                GeoPoint('N4825.8E00213.8', normalizer=dm_normalizer))
            self.assertEqual(
                points[-1],
                GeoPoint('N4843.4E00222.8', normalizer=dm_normalizer))

    def test_wpt_coordinates_alternate_af011_22Mar2016(self):
        with open(DATADIR + '/AF011_KJFK-LFPG_22Mar2016_02:45z_OFP_8_0_1.txt',
                  'r') as f:
            ofp = OFP(f.read())
            points = list(ofp.wpt_coordinates_alternate())
            self.assertEqual(
                points[0],
                GeoPoint('N4900.6E00232.9', normalizer=dm_normalizer))
            self.assertEqual(
                points[1],
                GeoPoint('N4825.8E00213.8', normalizer=dm_normalizer))
            self.assertEqual(
                points[-1],
                GeoPoint('N4843.4E00222.8', normalizer=dm_normalizer))

    @patch_object(OFP, 'log_error')
    def test_missing_wpt_coordinates(self, logger):
        ofp = OFP('blabla blabla')
        with self.assertRaises(KeyboardInterrupt):
            list(ofp.wpt_coordinates())
        logger.assert_called_with('WPT COORDINATES not found')

    @patch_object(OFP, 'log_error')
    def test_missing_wpt_coordinates_alternate(self, logger):
        ofp = OFP('blabla blabla')
        self.assertFalse(list(ofp.wpt_coordinates_alternate()))
        logger.assert_called_with('WPT COORDINATES not found')

    def test_missing_tracks(self):
        ofp = OFP('blabla blabla')
        self.assertEqual(list(ofp.tracks), [])
        with self.assertRaises(LookupError):
            ofp.tracks_iterator()

    def test_tracks(self):
        with open(DATADIR + '/KJFK-LFPG 27Mar2015 05:45z OFP.txt', 'r') as f:
            ofp = OFP(f.read())
        tracks = list(ofp.tracks)
        self.assertEqual(len(tracks), 9)
        self.assertEqual(
            tracks[0],
            Route([
                GeoPoint((56.000000, -20.000000)),
                GeoPoint((57.000000, -30.000000)),
                GeoPoint((58.000000, -40.000000)),
                GeoPoint((58.000000, -50.000000))])
        )
        self.assertEqual(
            tracks[-1],
            Route([
                GeoPoint((42.000000, -40.000000)),
                GeoPoint((38.000000, -50.000000)),
                GeoPoint((33.000000, -60.000000))])
        )
        for p in tracks[0]:
            self.assertTrue(p.name)
        self.assertTrue(tracks[0].name.endswith('A'))
        self.assertTrue(tracks[-1].name.endswith('J'))

    def tests_tracks_rlat_new_format(self):
        with open(DATADIR + '/AF009_KJFK-LFPG_18Mar2016_04:55z_OFP_12_0_1.txt',
                  'r') as f:
            ofp = OFP(f.read())
            tracks = list(ofp.tracks)
            self.assertEqual(len(tracks), 7)
            self.assertEqual(
                tracks[0],
                Route([
                    GeoPoint((50, -50)),
                    GeoPoint((51, -40)),
                    GeoPoint((52, -30)),
                    GeoPoint((53, -20))])
            )
            self.assertEqual(
                tracks[2],
                Route([
                    GeoPoint((48.5, -50)),
                    GeoPoint((49.5, -40)),
                    GeoPoint((50.5, -30)),
                    GeoPoint((51.5, -20))])
            )
            self.assertTrue(tracks[0].name.endswith('T'))
            self.assertTrue(tracks[-1].name.endswith('Z'))

    def tests_tracks_with_page_break(self):
        with open(DATADIR + '/AF011_KJFK-LFPG_22Mar2016_02:45z_OFP_8_0_1.txt',
                  'r') as f:
            ofp = OFP(f.read())
            tracks = list(ofp.tracks)
            self.assertEqual(len(tracks), 8)
            self.assertEqual(
                tracks[0],
                Route([
                    GeoPoint((51, -50)),
                    GeoPoint((52, -40)),
                    GeoPoint((54, -30)),
                    GeoPoint((56, -20))])
            )
            self.assertEqual(tracks[6].name, 'NAT Y')
            self.assertEqual(
                tracks[6],  # Y
                Route([
                    GeoPoint((40, -60)),
                    GeoPoint((41, -50)),
                    GeoPoint((41, -40))])
            )
            self.assertEqual(tracks[4].name, 'NAT W')  # FPL Track
            self.assertEqual(
                tracks[4],  # W
                Route([
                    GeoPoint((46.500000, -52.000000), name="PORTI"),
                    GeoPoint((47, -50)),
                    GeoPoint((48, -40)),
                    GeoPoint((50, -30)),
                    GeoPoint((52, -20)),
                    GeoPoint((52.000000, -15.000000), name="LIMRI"),
                    GeoPoint((52.000000, -14.000000), name="XETBO"),
                ])
            )
            self.assertTrue(tracks[0].name.endswith('S'))
            self.assertTrue(tracks[-1].name.endswith('Z'))

    def test_infos(self):
        from datetime import datetime, timedelta, time
        from editolido.ofp import utc
        with open(DATADIR + '/KJFK-LFPG 27Mar2015 05:45z OFP.txt', 'r') as f:
            ofp = OFP(f.read())
        expected = {
            'flight': 'AF009',
            'destination': 'LFPG',
            'departure': 'KJFK',
            'datetime': datetime(2015, 3, 27, 5, 45, tzinfo=utc),
            'duration': time(5, 54, tzinfo=utc),
            'ofp': '9/0/1',
            'date': '27Mar2015',
            'alternates': ['LFPO'],
            'ralts': ['CYQX', 'EINN'],
            'taxitime': 0,
        }
        self.assertDictEqual(ofp.infos, expected)
        dt = ofp.infos['datetime']
        self.assertEqual(dt.tzname(), 'UTC')
        self.assertEqual(dt.utcoffset(), timedelta(0))

    def test_infos_af011_22Mar2016(self):
        from datetime import datetime, timedelta, time
        from editolido.ofp import utc
        with open(DATADIR + '/AF011_KJFK-LFPG_22Mar2016_02:45z_OFP_8_0_1.txt',
                  'r') as f:
            ofp = OFP(f.read())
        expected = {
            'flight': 'AF011',
            'destination': 'LFPG',
            'departure': 'KJFK',
            'datetime': datetime(2016, 3, 22, 2, 45, tzinfo=utc),
            'duration': time(6, 18, tzinfo=utc),
            'ofp': '8/0/1',
            'date': '22Mar2016',
            'ralts': ['LPLA', 'EINN'],
            'alternates': ['LFPO'],
            'taxitime': 0,
        }
        self.assertDictEqual(ofp.infos, expected)
        dt = ofp.infos['datetime']
        self.assertEqual(dt.tzname(), 'UTC')
        self.assertEqual(dt.utcoffset(), timedelta(0))

    def test_infos_af1753_28Mar2016(self):
        from datetime import datetime, timedelta, time
        from editolido.ofp import utc
        with open(DATADIR + '/AF1753_UKBB-LFPG_28Mar2016_12:15z_OFP13.txt',
                  'r') as f:
            ofp = OFP(f.read())
        expected = {
            'flight': 'AF1753',
            'departure': 'UKBB',
            'destination': 'LFPG',
            'datetime': datetime(2016, 3, 28, 12, 15, tzinfo=utc),
            'duration': time(2, 57, tzinfo=utc),
            'ofp': '13',
            'date': '28Mar2016',
            'alternates': ['LFOB'],
            'ralts': [],
            'taxitime': 0,
        }
        self.assertDictEqual(ofp.infos, expected)
        dt = ofp.infos['datetime']
        self.assertEqual(dt.tzname(), 'UTC')
        self.assertEqual(dt.utcoffset(), timedelta(0))

    def test_description(self):
        with open(DATADIR + '/KJFK-LFPG 27Mar2015 05:45z OFP.txt', 'r') as f:
            ofp = OFP(f.read())
        self.assertEqual(
            ofp.description,
            "AF009 KJFK-LFPG 27Mar2015 05:45z OFP 9/0/1"
        )

    @patch_object(OFP, 'log_error')
    def test_fpl_lookup_error(self, logger):
        ofp = OFP('')
        self.assertEqual(ofp.fpl, [])
        logger.assert_called_with('ATC FLIGHT PLAN not found')
        logger.reset_mock()

        ofp = OFP('ATC FLIGHT PLANblabla')
        self.assertEqual(ofp.fpl, [])
        logger.assert_called_with(
            'enclosing brackets not found in ATC FLIGHT PLAN')
        logger.reset_mock()

        ofp = OFP('ATC FLIGHT PLAN(blabla)')
        self.assertEqual(ofp.fpl, [])
        logger.assert_called_with('incomplete Flight Plan')
        logger.reset_mock()

    def test_fpl(self):
        with open(DATADIR + '/KJFK-LFPG 27Mar2015 05:45z OFP.txt', 'r') as f:
            ofp = OFP(f.read())
        self.assertEqual(
            ' '.join(ofp.fpl),
            "KJFK DCT GREKI DCT MARTN DCT EBONY/M084F350 N247A ALLRY/M084F370 "
            "DCT 51N050W 53N040W 55N030W 55N020W DCT RESNO DCT "
            "NETKI/N0479F350 DCT BAKUR/N0463F350 UN546 STU UP2 "
            "NIGIT UL18 SFD/N0414F250 UM605 BIBAX BIBAX7W LFPG"
        )

    def test_raw_fpl_text(self):
        with open(DATADIR + '/KJFK-LFPG 27Mar2015 05:45z OFP.txt', 'r') as f:
            ofp = OFP(f.read())
        self.assertEqual(
            ofp.raw_fpl_text(),
            '(FPL-AFR009-IS-B77W/H-SDE2E3FGHIJ3J5J6M1M2RWXY/LB1D1'
            '-KJFK0545-N0476F350 DCT GREKI DCT MARTN DCT EBONY/M084F350 N247A '
            'ALLRY/M084F370 DCT 51N050W 53N040W 55N030W 55N020W DCT RESNO DCT '
            'NETKI/N0479F350 DCT BAKUR/N0463F350 UN546 STU UP2 NIGIT UL18 '
            'SFD/N0414F250 UM605 BIBAX BIBAX7W-LFPG0554 LFPO-PBN/A1B1C1D1L1S1 '
            'DOF/150327 REG/FGSQB EET/KZBW0004 CZQM0047 CZQX0119 ALLRY0156 '
            '51N050W0205 53N040W0247 EGGX0328 55N020W0403 RESNO0420 NETKI0423 '
            'EISN0432 EGTT0457 LFFF0526 SEL/HPLM OPR/AFR RALT/CYQX EINN '
            'RVR/100 RMK/ACAS)',
        )

    def test_fpl_route(self):
        with open(DATADIR + '/KJFK-LFPG 27Mar2015 05:45z OFP.txt', 'r') as f:
            ofp = OFP(f.read())
        self.assertEqual(
            ' '.join(ofp.fpl_route),
            "KJFK DCT GREKI DCT MARTN DCT EBONY N247A ALLRY "
            "DCT 51N050W 53N040W 55N030W 55N020W DCT RESNO DCT "
            "NETKI DCT BAKUR UN546 STU UP2 "
            "NIGIT UL18 SFD UM605 BIBAX BIBAX7W LFPG"
        )

    def test_fpl_route_af011_22Mar2016(self):
        with open(DATADIR + '/AF011_KJFK-LFPG_22Mar2016_02:45z_OFP_8_0_1.txt',
                  'r') as f:
            ofp = OFP(f.read())
        self.assertEqual(
            ' '.join(ofp.fpl_route),
            "KJFK DCT BETTE DCT ACK DCT KANNI N139A PORTI NATW "
            "LIMRI NATW XETBO DCT UNLID DCT LULOX UN84 NAKID UM25 UVSUV "
            "UM25 INGOR UM25 LUKIP LUKIP7E LFPG"
        )

    def test_lido_route(self):
        with open(DATADIR + '/KJFK-LFPG 27Mar2015 05:45z OFP.txt', 'r') as f:
            ofp = OFP(f.read())
        self.assertEqual(
            ' '.join(ofp.lido_route),
            'KJFK GREKI DCT MARTN DCT EBONY N247A ALLRY DCT 51N050W '
            '53N040W 55N030W 55N020W DCT RESNO DCT NETKI DCT BAKUR UN546 '
            'STU UP2 NIGIT UL18 SFD UM605 BIBAX N4918.0E00134.2 '
            'N4917.5E00145.4 N4915.7E00223.3 N4915.3E00230.9 '
            'N4913.9E00242.9 LFPG LFPO CYQX EINN'
        )

    def test_lido_route_af011_22Mar2016(self):
        with open(DATADIR + '/AF011_KJFK-LFPG_22Mar2016_02:45z_OFP_8_0_1.txt',
                  'r') as f:
            ofp = OFP(f.read())
        self.maxDiff = None
        self.assertEqual(
            ' '.join(ofp.lido_route),
            "KJFK N4036.7W07353.7 BETTE DCT ACK DCT KANNI N139A PORTI "
            "47N050W 48N040W 50N030W 52N020W "
            "LIMRI XETBO DCT UNLID DCT LULOX UN84 NAKID UM25 UVSUV "
            "UM25 INGOR UM25 LUKIP N4918.0E00134.2 N4917.5E00145.4 "
            "N4910.2E00150.4 LFPG LFPO LPLA EINN"
        )

    def test_lido_route_no_tracksnat(self):
        with open(DATADIR + '/KJFK-LFPG 27Mar2015 05:45z OFP.txt', 'r') as f:
            ofp = OFP(f.read())
        ofp.text = ofp.text.replace('TRACKSNAT', 'TRACKSNA*')
        self.maxDiff = None
        self.assertEqual(
            ' '.join(ofp.lido_route),
            'KJFK GREKI DCT MARTN DCT EBONY N247A ALLRY DCT 51N050W '
            '53N040W 55N030W 55N020W DCT RESNO DCT NETKI DCT BAKUR UN546 '
            'STU UP2 NIGIT UL18 SFD UM605 BIBAX N4918.0E00134.2 '
            'N4917.5E00145.4 N4915.7E00223.3 N4915.3E00230.9 '
            'N4913.9E00242.9 LFPG LFPO CYQX EINN'
        )

    @patch_object(OFP, 'log_error')
    def test_lido_route_no_fpl(self, logger):
        with open(DATADIR + '/KJFK-LFPG 27Mar2015 05:45z OFP.txt', 'r') as f:
            ofp = OFP(f.read())
        ofp.text = ofp.text.replace('ATC FLIGHT PLAN', 'ATC*FLIGHT*PLAN')
        self.assertEqual(
            ' '.join(ofp.lido_route),
            'KJFK GREKI MARTN EBONY ALLRY N5100.0W05000.0 N5300.0W04000.0 '
            'N5500.0W03000.0 N5500.0W02000.0 RESNO NETKI BAKUR STU NUMPO '
            'OKESI BEDEK NIGIT VAPID MID SFD WAFFU HARDY XIDIL PETAX BIBAX '
            'KOLIV MOPAR N4915.7E00223.3 CRL N4913.9E00242.9 LFPG'
        )
        logger.assert_called_with('ATC FLIGHT PLAN not found')

    def test_lido_route_with_naty(self):
        with open(DATADIR + '/AF007_KJFK-LFPG_13Mar2016_00:15z_OFP_6_0_1.txt',
                  'r') as f:
            ofp = OFP(f.read())
        self.maxDiff = None
        self.assertEqual(
            ' '.join(ofp.lido_route),
            'KJFK HAPIE DCT YAHOO DCT DOVEY 42N060W 43N050W 46N040W 49N030W '
            '49N020W BEDRA NERTU DCT TAKAS UN490 MOSIS UN491 BETUV UY111 '
            'JSY UY111 INGOR UM25 LUKIP N4918.0E00134.2 '
            'N4917.5E00145.4 N4910.2E00150.4 LFPG LFPO CYYT EINN'
        )

    @patch_object(OFP, 'log_error')
    def test_lido_route_with_naty_no_fpl(self, logger):
        with open(DATADIR + '/AF007_KJFK-LFPG_13Mar2016_00:15z_OFP_6_0_1.txt',
                  'r') as f:
            ofp = OFP(f.read())
        ofp.text = ofp.text.replace('ATC FLIGHT PLAN', 'ATC*FLIGHT*PLAN')
        self.assertEqual(
            ' '.join(ofp.lido_route),
            'KJFK HAPIE YAHOO DOVEY N4200.0W06000.0 N4300.0W05000.0 '
            'N4600.0W04000.0 N4900.0W03000.0 N4900.0W02000.0 BEDRA NERTU '
            'TAKAS ALUTA MOSIS DEKOR NERLA RUSIB BETUV JSY INGOR LUKIP '
            'KOLIV MOPAR N4910.2E00150.4 LFPG'
        )
        logger.assert_called_with('ATC FLIGHT PLAN not found')

    def test_lido_route_with_naty_no_tracksnat(self):
        with open(DATADIR + '/AF007_KJFK-LFPG_13Mar2016_00:15z_OFP_6_0_1.txt',
                  'r') as f:
            ofp = OFP(f.read())
        ofp.text = ofp.text.replace('TRACKSNAT', 'TRACKSNA*')
        self.maxDiff = None
        self.assertEqual(
            ' '.join(ofp.lido_route),
            'KJFK HAPIE DCT YAHOO DCT DOVEY NATY NERTU DCT TAKAS UN490 '
            'MOSIS UN491 BETUV UY111 '
            'JSY UY111 INGOR UM25 LUKIP N4918.0E00134.2 '
            'N4917.5E00145.4 N4910.2E00150.4 LFPG LFPO CYYT EINN'
        )

    def test_lido_route_ofp374_22Jul2016(self):
        """
        Ensure all waypoints and in the good order
        """
        with open(DATADIR + '/AF374_LFPG-CYVR_22Jul2016_08:45z_OFP_8_0_1.txt',
                  'r') as f:
            ofp = OFP(f.read())
        self.maxDiff = None
        self.assertEqual(
            ' '.join(ofp.lido_route),
            'LFPG N4900.9E00225.0 N4907.1E00219.2 ATREX UT225 VESAN UL613 '
            'SOVAT UL613 TLA UN601 STN UN610 BARKU UN610 RATSU DCT '
            '66N020W 68N030W 69N040W 70N050W 70N060W DCT ADSAM DCT 69N080W '
            '6730N09000W DCT ALKAP DCT 60N110W 55N117W DCT BOOTH '
            'N4928.2W12210.4 N4924.1W12220.9 N4916.8W12239.1 N4914.4W12254.1 '
            'N4915.2W12300.4 N4916.2W12307.9 N4917.6W12319.9 N4919.1W12331.9 '
            'N4914.7W12333.1 CYVR KSEA BIKF CYYR CYZF'
        )

    def test_wpt_ofp374_22Jul2016(self):
        """
        Ensure all waypoints and in the good order
        """
        with open(DATADIR + '/AF374_LFPG-CYVR_22Jul2016_08:45z_OFP_8_0_1.txt',
                  'r') as f:
            ofp = OFP(f.read())
            self.assertEqual(
                ' '.join([p.dm for p in ofp.route]),
                'N4900.6E00232.9 N4900.9E00225.0 N4907.1E00219.2 '
                'N4947.1E00222.1 N5022.3E00201.6 N5039.4E00138.2 '
                'N5046.8E00128.0 N5103.9E00104.0 N5201.6W00001.3 '
                'N5218.5W00016.2 N5300.6W00054.1 N5325.1W00116.8 '
                'N5344.1W00134.8 N5408.9W00158.8 N5530.0W00321.2 '
                'N5627.8W00418.4 N5641.7W00432.7 N5812.4W00611.0 '
                'N6001.2W00834.1 N6036.3W00924.6 N6100.0W01000.0 '
                'N6600.0W02000.0 N6800.0W03000.0 N6900.0W04000.0 '
                'N7000.0W05000.0 N7000.0W06000.0 N6955.3W06313.2 '
                'N6900.0W08000.0 N6730.0W09000.0 N6227.6W10621.0 '
                'N6000.0W11000.0 N5500.0W11700.0 N4931.3W12202.7 '
                'N4928.2W12210.4 N4924.1W12220.9 N4916.8W12239.1 '
                'N4914.4W12254.1 N4915.2W12300.4 N4916.2W12307.9 '
                'N4917.6W12319.9 N4919.1W12331.9 N4914.7W12333.1 '
                'N4911.7W12311.0'
            )

    def test_lido_route_af1753_28Mar2016(self):
        with open(DATADIR + '/AF1753_UKBB-LFPG_28Mar2016_12:15z_OFP13.txt',
                  'r') as f:
            ofp = OFP(f.read())
        self.maxDiff = None
        self.assertEqual(
            ' '.join(ofp.lido_route),
            'UKBB N5030.6E03051.1 N5032.0E03039.8 N5024.3E03017.3 '
            'KR P27 PEVOT T708 GIDNO T708 DIBED L984 OKG UL984 NOSPA DCT '
            'IDOSA UN857 RAPOR UZ157 VEDUS N4935.8E00404.0 N4928.5E00346.7 '
            'N4927.0E00337.9 N4925.2E00327.1 N4916.5E00319.6 LFPG LFOB'
        )

    def test_fpl_route_af6752_05Feb2017(self):
        filepath = DATADIR + '/AF6752_FMEE-FMMI_05Feb2017_11:50z_OFP_5_0_1.txt'
        with open(filepath, 'r') as f:
            ofp = OFP(f.read())
        self.assertEqual(
            ' '.join(ofp.fpl_route),
            "FMEE UNKIK4C UNKIK UA401 TE TE1Z FMMI"
        )

    def test_lido_route_af6752_05Feb2017(self):
        filepath = DATADIR + '/AF6752_FMEE-FMMI_05Feb2017_11:50z_OFP_5_0_1.txt'
        with open(filepath, 'r') as f:
            ofp = OFP(f.read())
        self.maxDiff = None
        self.assertEqual(
            ' '.join(ofp.lido_route),
            'FMEE UNKIK UA401 TE S1847.0E04723.6 S1847.6E04727.3 FMMI HTDA'
        )

    def test_tracks_af6752_05Feb2017_empty(self):
        filepath = DATADIR + '/AF6752_FMEE-FMMI_05Feb2017_11:50z_OFP_5_0_1.txt'
        with open(filepath, 'r') as f:
            ofp = OFP(f.read())
        self.maxDiff = None
        self.assertEqual(
            ' '.join(ofp.tracks),
            ''
        )

    def test_taxitime_af6752_05Feb2017(self):
        filepath = DATADIR + '/AF6752_FMEE-FMMI_05Feb2017_11:50z_OFP_5_0_1.txt'
        with open(filepath, 'r') as f:
            ofp = OFP(f.read())
        self.assertEqual(
            ofp.infos['taxitime'],
            8
        )

    def test_extract_coordinates_from_text(self):
        filepath = DATADIR + '/pdf_coordinates_copied_from_goodreader.txt'
        with open(filepath, 'r') as f:
            ofp = OFP(f.read())
        self.assertEqual(len(list(ofp.wpt_coordinates(tag=None))), 80)
        self.assertEqual(
            len(list(ofp.wpt_coordinates_alternate(start=None, end=None))), 9)
