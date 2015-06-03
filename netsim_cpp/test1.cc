
#include "vectorl.hh"

using namespace boost;
using namespace boost::multi_array_types;
using namespace std;
using namespace vectorl;

struct foo
{
	struct {
		multi_array<int, 2>  x { extents[3][4] };
		multi_array<int, 1>  y { extents[1] };
	} mod1;
};


void on_foo()
{
	multi_array<int, 2>  x { extents[3][4] };

	for(size_t i=0; i< x.dimensionality; i++)
		cout << x.shape()[i] << endl;

	for(int i=0; i<3; i++)
		for(int j=0; j<4; j++) {
			x[i][j] = i+j;
		}

	multi_array<int, 1>  y{ extents[1] };
	y[0]=2;

	foo z;

	cout << x << endl;

	cout << x[indices[index_range(2,-1,-2)][index_range(0,4)] ] << endl;
	cout << z.mod1.x << endl;
}





int main()
{
	on_foo();

	typedef boost::multi_array_types::index aindex;

	for(multi_iteration<aindex, 2> x{{4,3}}; x; ++x)
	{
		for(auto i : (*x)) {
			cout << i << " ";
		}
		cout << endl;
	}


	multi_array<int, 2> A { extents[2][2] };
	multi_array<int, 1> b { extents[2] };

	for(vectorl::multi_iteration<aindex, 2> I{{2, 2}} ;  I; ++I)
	{
		A(*I) =  ((*I)[0] == (*I)[1]) ? 0 : 1;
	}
	b[0] = 3;
	b[1] = 1;

	cout << "A=" << A << endl;
	cout << "b=" << b << endl;

	multi_array<int, 2> B { extents[2][2] };


	for(vectorl::multi_iteration<aindex, 2> I{{2,2}}; I; ++I)
	{
	//		sub_range< std::array<aindex,2> > subr = I.index().begin()+1;
		std::array<aindex, 1> bidx;
		bidx[0] = (*I)[1];
		B(*I) =  A(*I) + b( bidx );
	}

	cout << "B=" << B << endl;

	return 0;
}