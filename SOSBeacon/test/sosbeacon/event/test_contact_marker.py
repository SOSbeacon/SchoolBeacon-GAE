
import gaetest


class TestContactMarkerMerge(gaetest.TestCase):
    """Test that ContactMarker merge logic functions as expected."""

    def test_merge_non_ack(self):
        """Ensure merging two non-acked doesn't ack."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(acknowledged=False)
        right = ContactMarker(acknowledged=False)
        left.merge(right)
        self.assertFalse(left.acknowledged)

    def test_merge_ack_to_non_ack(self):
        """Ensure merging two non-acked doesn't ack."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(acknowledged=False)
        right = ContactMarker(acknowledged=True)
        left.merge(right)
        self.assertTrue(left.acknowledged)

    def test_merge_non_ack_to_ack(self):
        """Ensure merging two non-acked doesn't ack."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(acknowledged=True)
        right = ContactMarker(acknowledged=False)
        left.merge(right)
        self.assertTrue(left.acknowledged)

    def test_merge_acks(self):
        """Ensure merging two non-acked doesn't ack."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(acknowledged=True)
        right = ContactMarker(acknowledged=True)
        left.merge(right)
        self.assertTrue(left.acknowledged)

    def test_merge_unviewed(self):
        """Ensure merging two non-acked doesn't set view date."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker()
        right = ContactMarker()
        left.merge(right)
        self.assertEqual(0, left.last_viewed_date)

    def test_merge_last_viewed_date(self):
        """Ensure merging non-acked with acked sets view date."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(last_viewed_date=0)
        right = ContactMarker(last_viewed_date=12345)
        left.merge(right)
        self.assertEqual(12345, left.last_viewed_date)

    def test_merge_last_viewed_date_with_non_acked(self):
        """Ensure merging non-acked with acked sets view date."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(last_viewed_date=321123)
        right = ContactMarker(last_viewed_date=0)
        left.merge(right)
        self.assertEqual(321123, left.last_viewed_date)

    def test_merge_last_viewed_date_with_smaller(self):
        """Ensure merging non-acked with acked sets view date."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(last_viewed_date=100)
        right = ContactMarker(last_viewed_date=10)
        left.merge(right)
        self.assertEqual(100, left.last_viewed_date)

    def test_merge_last_viewed_date_with_larger(self):
        """Ensure merging non-acked with acked sets view date."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(last_viewed_date=20)
        right = ContactMarker(last_viewed_date=200)
        left.merge(right)
        self.assertEqual(200, left.last_viewed_date)

    def test_merge_last_viewed_date_with_same(self):
        """Ensure merging non-acked with acked sets view date."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(last_viewed_date=334)
        right = ContactMarker(last_viewed_date=334)
        left.merge(right)
        self.assertEqual(334, left.last_viewed_date)

    def test_merge_no_short_ids(self):
        """Ensure merging with no short ids."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker()
        right = ContactMarker()
        left.merge(right)
        self.assertEqual(None, left.short_id)

    def test_merge_new_short_id(self):
        """Ensure merging with no short id with new short id."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker()
        right = ContactMarker(short_id='N123')
        left.merge(right)
        self.assertEqual('N123', left.short_id)

    def test_merge_missing_short_id(self):
        """Ensure merging short id with no short id."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(short_id='N213')
        right = ContactMarker()
        left.merge(right)
        self.assertEqual('N213', left.short_id)

    def test_merge_different_short_id(self):
        """Ensure merging with different short ids."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(short_id='N123')
        right = ContactMarker(short_id='Z312')
        left.merge(right)
        self.assertEqual('N123', left.short_id)

    def test_merge_no_names(self):
        """Ensure merging with no names."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker()
        right = ContactMarker()
        left.merge(right)
        self.assertEqual(None, left.name)

    def test_merge_new_name(self):
        """Ensure merging no name with new name."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker()
        right = ContactMarker(name='Name 1')
        left.merge(right)
        self.assertEqual('Name 1', left.name)

    def test_merge_missing_name(self):
        """Ensure merging missing name with name."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(name='Name 2')
        right = ContactMarker()
        left.merge(right)
        self.assertEqual('Name 2', left.name)

    def test_merge_different_name(self):
        """Ensure merging with two different names."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(name='Name 3')
        right = ContactMarker(name='Name 4')
        left.merge(right)
        self.assertEqual('Name 3', left.name)

    def test_merge_no_students(self):
        """Ensure merging with no students."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker()
        right = ContactMarker()
        left.merge(right)
        self.assertEqual([], left.students)

    def test_merge_students_with_no_students(self):
        """Ensure merging students with no students."""
        from sosbeacon.event.contact_marker import ContactMarker

        students = [
            ('123312', 'Sam Smith', 123432),
            ('312130', 'John Jones', 312123),
            ('544312', 'Billy Bob', 348223)
        ]

        left = ContactMarker(students=students)
        right = ContactMarker()
        left.merge(right)
        self.assertEqual(sorted(students), sorted(left.students))

    def test_merge_no_students_with_students(self):
        """Ensure merging no students with students."""
        from sosbeacon.event.contact_marker import ContactMarker

        students = [
            ('123312', 'Sam Smith', 123432),
            ('312130', 'John Jones', 312123),
            ('544312', 'Billy Bob', 348223)
        ]

        left = ContactMarker()
        right = ContactMarker(students=students)
        left.merge(right)
        self.assertEqual(sorted(students), sorted(left.students))

    def test_merge_students(self):
        """Ensure merging students."""
        from sosbeacon.event.contact_marker import ContactMarker

        students_1 = [
            ('123312', 'Sam Smith', 123432),
            ('312130', 'John Jones', 312123),
            ('544312', 'Billy Bob', 348223)
        ]

        students_2 = [
            ('848423', 'Frank Frankton', 953342),
        ]

        left = ContactMarker(students=students_1)
        right = ContactMarker(students=students_2)
        left.merge(right)
        self.assertEqual(sorted(students_1 + students_2), sorted(left.students))

    def test_merge_overlapping_students(self):
        """Ensure merging students with overlaps."""
        from sosbeacon.event.contact_marker import ContactMarker

        base_students = [
            ('312130', 'John Jones', 312123),
            ('544312', 'Billy Bob', 348223)
        ]

        students_1 = base_students + [('123312', 'Sam Smith', 123432)]
        students_2 = base_students + [('848423', 'Frank Frankton', 953342)]

        left = ContactMarker(students=students_1)
        right = ContactMarker(students=students_2)
        left.merge(right)
        self.assertEqual(sorted(set(students_1 + students_2)),
                         sorted(left.students))

